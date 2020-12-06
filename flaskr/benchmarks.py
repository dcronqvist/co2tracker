import flask
from flask import request, jsonify, make_response
from flaskr import app, check_payload
from flaskr.db import coll_benchmarks
import datetime
import json

# SEARCH ALL BENCHMARKS FOR PRODUCT
b_all_sample = {
    "product": ["str"]
}
"""
CURL-FRIENDLY TEST:
$ curl -d '{"product": "accumulator"}' -H "Content-Type: application/json" -X POST http://localhost:5000/benchmarks/get/all
"""
@app.route("/benchmarks/get/all", methods=["POST"])
def benchmarks_all():
    query = request.get_json() # Get query as json
    check, msg = check_payload(b_all_sample, query) # Check payload

    if check:
        found = coll_benchmarks.find({'product': query["product"]}) # find all benchmarks for this product
        l = list(found)
        if len(l) > 0: # If there are more than 0 found benchmarks, return them
            return make_response(jsonify(l), 200)
        else: # if there were no found benchmarks for that product, then return "No benchmarks found"
            return make_response(jsonify("No benchmarks found."), 404)
    else:
        # If the payload doesn't pass payload check, return 400
        return make_response(jsonify(msg), 400)

# SEARCH ALL BENCHMARKS FOR PRODUCT
b_latest_sample = {
    "product": ["str"]
}
"""
CURL-FRIENDLY TEST:
$ curl -d '{"product": "accumulator"}' -H "Content-Type: application/json" -X POST http://localhost:5000/benchmarks/get/latest
"""
@app.route("/benchmarks/get/latest", methods=["POST"])
def benchmarks_latest():
    query = request.get_json() # Get query as json
    check, msg = check_payload(b_latest_sample, query) # Check payload

    if check:
        found = coll_benchmarks.find_one({'product': query["product"], 'latest_benchmark': True}) # find all benchmarks for this product
        if found: # If there was a benchmark found.
            return make_response(jsonify(found), 200)
        else: # if there was no found benchmark for that product, then return "No benchmark found"
            return make_response(jsonify("No benchmark found."), 404)
    else:
        # If the payload doesn't pass payload check, return 400
        return make_response(jsonify(msg), 400)