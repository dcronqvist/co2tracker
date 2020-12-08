import flask
from flask import request, jsonify, make_response
from flaskr import app, check_payload
from flaskr.db import coll_products, coll_transports
import datetime
import json
from flaskr.bench_util import get_chain_impact, insert_benchmark
from datetime import datetime as dt

"""
SAMPLE CREATE TRANSPORT OBJECT
Following sample object conventions.
 - keys with lists of strings specify which types are allowed for that specific key in the payload
 - keys with strings only allow that specific string to the specified in the payload
 - keys with objects are recursively checked with the above two rules
"""
transport_create_sample = {
    '_id': ["int"], # e.g. 1
    'type': "transport", # will always be transport
    'type_description': ["str"], # e.g. "train"
    'impact': {
        'co2_per_kg_km': ['int', 'float'],
        'measurement_error': ['int', 'float'],
        'distance_travelled': ['int', 'float'],
        'energy_sources': ['list'],
    },
    'start_lat': ["float", "int"],
    'start_lon': ["float", "int"],
    'end_lat': ["float", "int"],
    'end_lon': ["float", "int"],
    'max_weight': ["float", "int"]
}

"""
CURL-FRIENDLY TEST:
$ curl -X POST -d '{ "_id": 100, "type": "transport", "type_description": "train", "impact": {"co2_per_kg_km":0.005, "measurement_error": 0.11, "distance_travelled": 14000, "energy_sources":["nuclear", "coal"]}, "start_lat": 27.19, "start_lon": 113.69, "end_lat": 27.49, "end_lon": 119.66, "max_weight": 3219}' -H "Content-Type: application/json" 127.0.0.1:5000/transports/create
"""

@app.route('/transports/create', methods=['POST'])
def transports_create():
    query = request.get_json()
    check, msg = check_payload(transport_create_sample, query)
    if check:
        # Check whether transport id already exists in DB
        find = coll_transports.find_one({'_id': query['_id']})
        # We add the transport if the id doesn't exist in DB
        if find == None:
            coll_transports.insert_one(query)
            return make_response(jsonify(query), 200)
        else:
            return make_response(jsonify('ERROR: ID ' + str(query['_id']) + ' already exists'), 400)
    else:
        # Something went wrong when checking payload. Return error. 
        return make_response(jsonify(msg), 400)


# SEARCH TRANSPORTS BY ID'S
transport_search_sample_id = {
    "_id": ["list"],
}

"""
CURL-FRIENDLY TEST:
$ curl -X POST -d '{ "_id": [1,2] }' -H "Content-Type: application/json" 127.0.0.1:5000/transports/search/id
"""

@app.route('/transports/search/id', methods=['POST'])
def transports_get_id():
    query = request.get_json()
    succ, msg = check_payload(transport_search_sample_id, query)

    if succ:
        found = coll_transports.find({'_id': {'$in': query['_id']}}) # find products with any of the id's provided
        l = (list(found))
        if len(l) == 0: # if none found, return error
            return make_response(jsonify("No transports found."), 404)
        return make_response(jsonify(l), 200)

    return make_response(jsonify(msg), 400)



