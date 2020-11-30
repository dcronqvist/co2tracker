import flask
from flask import request, jsonify, make_response
from flaskr import app
from flaskr.db import collection
import datetime
import json

def check_payload(sample, payload):
    """
    Loop through all keys in sample, make sure they all exist in the payload.
    Type check all keys to make sure they match. Lists are harder, since 
    there isn't an implementation to check if the elements are of the correct type.
    TODO: ADD TYPE CHECKING FOR ELEMENTS IN LISTS
    """
    for key in sample:
        if payload and hasattr(payload, "__iter__"):
            if key in payload:
                if type(sample[key]) == list:
                    # Here we type check for all possible allowed types in the list in the sample object.
                    ok_types = [eval(t) for t in sample[key]]
                    if not (type(payload[key]) in ok_types):
                        return False, f"ERROR: On key '{key}', expected type(s) '{ok_types}', got '{type(payload[key])}'."
                elif type(sample[key]) == str:
                    # If it is a string in the sample, then that means that the key must match EXACT
                    if not (sample[key] == payload[key]):
                        return False, f"ERROR: On key '{key}', expected '{sample[key]}', got '{payload[key]}'."
                else:
                    # The sample is an object, recursively check downwards
                    succ, msg = check_payload(sample[key], payload[key])
                    if not succ:
                        return False, msg
            else:
                return False, f"ERROR: Missing key '{key}'"
        else:
            return False, f"ERROR: Payload is null or in wrong format."
    return True, "Payload matches sample."


# CREATE PRODUCT
"""
SAMPLE CREATE PRODUCT OBJECT
Following sample object conventions.
 - keys with lists of strings specify which types are allowed for that specific key in the payload
 - keys with strings only allow that specific string to the specified in the payload
 - keys with objects are recursively checked with the above two rules
"""
product_create_sample = {
    '_id': ["str"], # e.g. "IKEA-BILLY-5"
    'type': "product", # will always be product
    'tags': ["list"], # e.g. ["furniture", "shelf", "wood"]
    'type_description': ["str"], # "Assembly"
    'prod_name': ["str"], # e.g. "Billy Shelf"
    'weight': ["float", "int"], # e.g. 12.81
    'benchmark': {
        "self_impact": {
            "co2": ["float", "int"], # e.g. 292.62
            "measurement_error": ["float"], # e.g. 0.05 -> 5% error margin
            "energy_sources": ["list"] # e.g. ["Solar", "Nuclear", "Wind"]
        },
        "date": ["str"], # e.g. "2020-11-30-22:50:51"
        "subproducts": ["list"],# should be a list of objects with "product" and "transport" keys
    }
}
"""
CURL-FRIENDLY TEST:
$ curl -X POST -d '{ "_id": "IKEA-BILLY", "weight": 25, "type": "product", "tags": ["Furniture"], "type_description": "Assembly", "prod_name": "IKEA Billy Shelf", "benchmark": { "self_impact": { "co2": 5.1, "measurement_error": 0.05, "energy_sources": ["Solar", "Nuclear", "Wind"] }, "date": "2020-12-01-00:05:32", "subproducts": [] } }' -H "Content-Type: application/json" 127.0.0.1:5000/products/create
"""
@app.route('/products/create', methods=["POST"]) 
def products_create():
    query = request.get_json()
    check, msg = check_payload(product_create_sample, query)
    if check:
        # All good, create product.
        # TODO: ADD PRODUCT TO DATABASE
        return make_response(jsonify(query), 200)
        pass
    else:
        # Something went wrong when checking payload. Return error.
        return make_response(jsonify(msg), 400)


# SEARCH PRODUCTS
"""
SAMPLE CREATE PRODUCT OBJECT
Following sample object conventions.
 - keys with lists of strings specify which types are allowed for that specific key in the payload
 - keys with strings only allow that specific string to the specified in the payload
 - keys with objects are recursively checked with the above two rules
"""
product_search_sample_1 = {
    "tags": ["list"],
}
product_search_sample_2 = {
    "_id": ["list"],
}
"""
CURL-FRIENDLY TEST:
$ curl -X POST -d '{ "tags": ["iron", "green"] }' -H "Content-Type: application/json" 127.0.0.1:5000/products/search
$ curl -X POST -d '{ "tags": ["iron", "green", "headphones"] }' -H "Content-Type: application/json" 127.0.0.1:5000/products/search
"""
@app.route('/products/search', methods=["POST"])
def products_search():
    query = request.get_json() # get query in json-format

    succ1, msg1 = check_payload(product_search_sample_1, query)
    succ2, msg2 = check_payload(product_search_sample_2, query)

    if succ1 or succ2:
        if 'tags' in query: 
            collection.create_index('tags') # create tag-index
            found = collection.find({'tags': { '$all': query['tags']}}) # find products which have ALL the specified tags
            l = list(found)
            if len(l) == 0:
                return make_response(jsonify("No products found."), 404)
            return make_response(jsonify(l), 200)
        if '_id' in query:
            found = collection.find({'_id': {'$in': query['_id']}}) # find products with any of the id's provided
            l = (list(found))
            if len(l) == 0: # if none found, return error
                return make_response(jsonify("No products found."), 404)
            return make_response(jsonify(l), 200)
    
    if succ1 and not succ2:
        return make_response(jsonify(msg2), 400)
    else:
        return make_response(jsonify(msg1), 400)




