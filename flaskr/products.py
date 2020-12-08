import flask
from flask import request, jsonify, make_response
from flaskr import app, check_payload
from flaskr.db import coll_products
import datetime
import json
from flaskr.bench_util import get_chain_impact, insert_benchmark
from datetime import datetime as dt

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
    'tags': ["list:str"], # e.g. ["furniture", "shelf", "wood"]
    'type_description': ["str"], # "Assembly"
    'prod_name': ["str"], # e.g. "Billy Shelf"
    'kg_per_unit': ["float", "int"], # e.g. 12.81
    'unit': ["str"],
    'benchmark': {
        "self_impact": {
            "co2": ["float", "int"], # e.g. 292.62
            "measurement_error": ["float"], # e.g. 0.05 -> 5% error margin
            "energy_sources": ["list:str"] # e.g. ["Solar", "Nuclear", "Wind"]
        },
        "date": ["str"], # e.g. "2020-11-30-22:50:51"
        "sub_products": [
            {
                "product": ["str"],
                "unit_amount": ["float", "int"],
                "transport": ["int"]
            }
        ]
    }
}
"""
CURL-FRIENDLY TEST:
$ curl -X POST -d '{ "_id": "IKEA-BILLY", "kg_per_unit": 25, "unit": "piece", "type": "product", "tags": ["Furniture"], "type_description": "Assembly", "prod_name": "IKEA Billy Shelf", "benchmark": { "self_impact": { "co2": 5.1, "measurement_error": 0.05, "energy_sources": ["Solar", "Nuclear", "Wind"] }, "date": "2020-12-01-00:05:32", "sub_products": [] } }' -H "Content-Type: application/json" 127.0.0.1:5000/products/create
"""
@app.route('/products/create', methods=["POST"]) 
def products_create():
    query = request.get_json()
    check, msg = check_payload(product_create_sample, query)
    if check:
        prod = {
            "_id": query["_id"].upper(),
            "type": "product",
            "tags": [tag.lower() for tag in query["tags"]],
            "type_description": query["type_description"].lower(),
            "prod_name": query["prod_name"]
        }
        # All good, create product.

        find = coll_products.find_one({'_id': query['_id'].upper()})
        # If find returns the product, we do none of the below (product already exists)
        
        if find == None:
            coll_products.insert_one(prod)

            benchmark = {
                "date": dt.today().strftime("%Y-%m-%d"),
                "product": prod["_id"],
                "_id": prod["_id"] + "-" + dt.today().strftime("%Y-%m-%d") + "-" + dt.now().strftime("%H:%M:%S"),
                "kg_per_unit": query["kg_per_unit"],
                "unit": query["unit"],
                "self_impact": {
                    "co2": query["benchmark"]["self_impact"]["co2"],
                    "measurement_error": query["benchmark"]["self_impact"]["measurement_error"],
                    "energy_sources": [es.lower() for es in query["benchmark"]["self_impact"]["energy_sources"]]
                },
                "chain_impact": {
                    "co2": 0,
                    "measurement_error": 0
                },
                "sub_products": query["benchmark"]["sub_products"],
                "latest_benchmark": True
            }
            insert_benchmark(benchmark)
            return make_response(jsonify(prod), 200)
            pass
        else:
            return make_response(jsonify('ERROR: ID ' + str(query['_id']).upper() + ' already exists'), 400)
    else:
        # Something went wrong when checking payload. Return error.
        return make_response(jsonify(msg), 400)


# SEARCH PRODUCTS BY TAGS
product_search_sample_tags = {
    "tags": ["list:str"],
}
"""
CURL-FRIENDLY TEST:
$ curl -X POST -d '{ "tags": ["iron", "green"] }' -H "Content-Type: application/json" 127.0.0.1:5000/products/search/tags
"""
@app.route('/products/search/tags', methods=["POST"])
def products_search_by_tag():
    query = request.get_json() # get query in json-format
    succ, msg = check_payload(product_search_sample_tags, query)

    if succ:
        coll_products.create_index('tags') # create tag-index
        found = coll_products.find({'tags': { '$all': query['tags']}}) # find products which have ALL the specified tags
        l = list(found)
        if len(l) == 0:
            return make_response(jsonify("No products found."), 404)
        return make_response(jsonify(l), 200)
    
    return make_response(jsonify(msg), 400)


# SEARCH PRODUCTS BY ID'S
product_search_sample_id = {
    "_id": ["list:str"],
}
"""
CURL-FRIENDLY TEST:
$ curl -X POST -d '{ "_id": ["accumulator", "steel-axe"] }' -H "Content-Type: application/json" 127.0.0.1:5000/products/search/id
"""
@app.route('/products/search/id', methods=["POST"])
def products_search_by_id():
    query = request.get_json() # get query in json-format
    succ, msg = check_payload(product_search_sample_id, query)

    if succ:
        found = coll_products.find({'_id': {'$in': query['_id']}}) # find products with any of the id's provided
        l = (list(found))
        if len(l) == 0: # if none found, return error
            return make_response(jsonify("No products found."), 404)
        return make_response(jsonify(l), 200)

    return make_response(jsonify(msg), 400)




