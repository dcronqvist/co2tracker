import flask
from flask import request, jsonify, make_response
from flaskr import app
from flaskr.db import collection
import datetime

sampleobject = { # sample object with all the parameters
    'type': "product",
    'tags': None,
    'type_description': "",
    'impact': {
        'co2': None,
        'measurement_error': None,
        'energy_sources': ""
    },
    'prod_name': "",
    'prod_id': None,
    'weight': None,
    'benchmarks': {
    }
}

@app.route('/add', methods=["POST"])
def add():
    query = request.get_json()
    for key in sampleobject: # we check if the inserted object has all the mandatory fields
        if key in query:
            continue
        else:
            return make_response(jsonify(query), 404) # return error if we find a field which doesn't match
    
    for key in sampleobject['impact']: # check if query.implact has all the mandatory fields
        if key in query['impact']:
            continue
        else:
            return make_response(jsonify(query), 404) # return error if we find a field which doesn't match

    # TBA - we need to add product to database here
    return make_response(jsonify(query), 200)



