import flask
from flask import request, jsonify, make_response
from flaskr import app, check_payload
from flaskr.db import coll_products
import datetime
import json
from flaskr.api_util import get_chain_impact, insert_benchmark, get_all_tags, get_all_product_ids
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
    '_id': ["str"],  # e.g. "IKEA-BILLY-5"
    'type': "product",  # will always be product
    'tags': ["list:str"],  # e.g. ["furniture", "shelf", "wood"]
    'type_description': ["str"],  # "Assembly"
    'prod_name': ["str"],  # e.g. "Billy Shelf"
    'kg_per_unit': ["float", "int"],  # e.g. 12.81
    'unit': ["str"],
    'benchmark': {
        "self_impact": {
            "co2": ["float", "int"],  # e.g. 292.62
            "measurement_error": ["float"],  # e.g. 0.05 -> 5% error margin
            "energy_sources": ["list:str"]  # e.g. ["Solar", "Nuclear", "Wind"]
        },
        "date": ["str"],  # e.g. "2020-11-30-22:50:51"
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
        if len(query["_id"]) > 2:
            prod = {
                "_id": query["_id"].lower(),
                "type": "product",
                "tags": [tag.lower() for tag in query["tags"]],
                "type_description": query["type_description"].lower(),
                "prod_name": query["prod_name"]
            }
            # All good, create product.

            find = coll_products.find_one({'_id': query['_id'].lower()})
            # If find returns the product, we do none of the below (product already exists)
            if find is None:
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
                return make_response(jsonify('ERROR: ID ' + str(query['_id']).lower() + ' already exists'), 400)
        else:
            return make_response(jsonify('ERROR: ID must be longer than 2 characters.'), 400)
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
    query = request.get_json()  # get query in json-format
    succ, msg = check_payload(product_search_sample_tags, query)

    if succ:
        coll_products.create_index('tags')  # create tag-index
        found = coll_products.find({'tags': { '$all': query['tags']}})  # find products which have ALL the specified tags
        li = list(found)
        if len(li) == 0:
            return make_response(jsonify("No products found."), 404)
        return make_response(jsonify(li), 200)
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
    query = request.get_json()  # get query in json-format
    succ, msg = check_payload(product_search_sample_id, query)

    if succ:
        found = coll_products.find({'_id': {'$in': [i.lower() for i in query['_id']] }})  # find products with any of the id's provided
        li = (list(found))
        if len(li) == 0:  # if none found, return error
            return make_response(jsonify("No products found."), 404)
        return make_response(jsonify(li), 200)

    return make_response(jsonify(msg), 400)


# GET ALL PRODUCT TAGS AND THEIR FREQUENCY OF USE
"""
CURL-FRIENDLY TEST:
$ curl 127.0.0.1:5000/products/tags/all
"""
@app.route('/products/tags/all', methods=["GET"])
def products_tags_all():
    return make_response(jsonify(get_all_tags()), 200)


# GET ALL PRODUCT IDS
"""
CURL-FRIENDLY TEST:
$ curl 127.0.0.1:5000/products/id/all
"""
@app.route('/products/id/all', methods=["GET"])
def products_id_all():
    return make_response(jsonify(get_all_product_ids()), 200)


# SEARCH PRODUCTS BY REGEX ON ID's
product_search_sample_id_regex = {
    "search": ["str"],
}
"""
CURL-FRIENDLY TEST:
$ curl -X POST -d '{ "search": "accumu" }' -H "Content-Type: application/json" 127.0.0.1:5000/products/search/id/regex
"""
@app.route('/products/search/id/regex', methods=["POST"])
def products_search_by_id_regex():
    query = request.get_json()  # get query in json-format
    succ, msg = check_payload(product_search_sample_id_regex, query)

    if succ:
        found = coll_products.find({ "_id": { "$regex": query["search"], "$options": "i" } }, {"_id": 1})  # find products that matches on regex search
        li = [prod["_id"] for prod in list(found)]
        if len(li) == 0:  # if none found, return empty array
            return make_response(jsonify([]), 200)
        return make_response(jsonify(li), 200)

    return make_response(jsonify(msg), 400)


# SEARCH PRODUCTS BY REGEX ON PROD_NAMES's
product_search_sample_id_regex = {
    "search": ["str"],
}
"""
CURL-FRIENDLY TEST:
$ curl -X POST -d '{ "search": "accumu" }' -H "Content-Type: application/json" 127.0.0.1:5000/products/search/name/regex
"""
@app.route('/products/search/name/regex', methods=["POST"])
def products_search_by_name_regex():
    query = request.get_json()  # get query in json-format
    succ, msg = check_payload(product_search_sample_id_regex, query)

    if succ:
        found = coll_products.find({ "prod_name": { "$regex": query["search"], "$options": "i" } }, {"_id": 1, "prod_name": 1})  # find products that matches on regex search
        d = dict()
        for prod in list(found):
            d[prod["_id"]] = prod["prod_name"]
        if len(d) == 0:  # if none found, return empty array
            return make_response(jsonify({}), 200)
        return make_response(jsonify(d), 200)
    return make_response(jsonify(msg), 400)
