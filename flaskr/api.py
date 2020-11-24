import flask
from flask import request, jsonify, make_response
from flaskr import app
from flaskr.db import collection
import datetime

sampleobject = { # sample object with all the parameters
    'type': "product",
    'tags': None,
    'type_description': "",
    'prod_name': "",
    'weight': None,
    'id': None,
    'benchmarks': {
    },
    'self_impact': {
        'co2': None,
        'measurement_error': None,
        'energy_sources': ""
    }
}

# ADD-ENDPOINT
@app.route('/add', methods=["POST"]) 
def add():
    query = request.get_json()
    for key in sampleobject: # we check if the inserted object has all the mandatory fields (all the fields in sampleobject above!)
        if key in query:
            continue
        else:
            return make_response(jsonify(query), 404) # return error if we find a field which doesn't match
    
    for key in sampleobject['self_impact']: # check if query.self_impact has all the mandatory fields (all the fields in sampleobject above!)
        if key in query['self_impact']:
            continue
        else:
            return make_response(jsonify(query), 404) # return error if we find a field which doesn't match

    # TBA - we need to add product to database here
    return make_response(jsonify(query), 200)

# GET-ENDPOINT
# possible parameters supplied to get-endpoint, ONLY ONE CAN BE PROVIDED AT A TIME:
# {
#   'tags': [ .. , .. , .. ]
#   '_id': ''
# }
@app.route('/get', methods=["POST"])
def get():
    query = request.get_json() # get query in json-format

    if 'tags' in query: 
        found = collection.find({'tags': { '$all': query['tags']}}) # find products with all the specified tags
        return make_response(jsonify(list(found)), 200)
    if '_id' in query:
        found = collection.find_one({'_id' : query['_id']})
        return make_response(jsonify(found), 200)
    return make_response(jsonify(None), 400)




