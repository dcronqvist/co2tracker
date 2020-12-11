import flask
from flask import request, jsonify, make_response
from flaskr import app, check_payload
from flaskr.db import coll_benchmarks, coll_products
from flaskr.api_util import create_chain_impact, add_benchmark
import datetime
import json
from datetime import datetime as dt

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
    query = request.get_json()  # Get query as json
    check, msg = check_payload(b_all_sample, query)  # Check payload

    if check:
        found = coll_benchmarks.find({'product': query["product"]})  # find all benchmarks for this product
        li = list(found)
        if len(li) > 0:  # If there are more than 0 found benchmarks, return them
            return make_response(jsonify(li), 200)
        else:  # if there were no found benchmarks for that product, then return "No benchmarks found"
            return make_response(jsonify("No benchmarks found."), 404)
    else:
        # If the payload doesn't pass payload check, return 400
        return make_response(jsonify(msg), 400)


# SEARCH LATEST BENCHMARK FOR PRODUCT
b_latest_sample = {
    "product": ["str"]
}
"""
CURL-FRIENDLY TEST:
$ curl -d '{"product": "accumulator"}' -H "Content-Type: application/json" -X POST http://localhost:5000/benchmarks/get/latest
"""
@app.route("/benchmarks/get/latest", methods=["POST"])
def benchmarks_latest():
    query = request.get_json()  # Get query as json
    check, msg = check_payload(b_latest_sample, query)  # Check payload

    if check:
        found = coll_benchmarks.find_one({'product': query["product"], 'latest_benchmark': True})  # find latest benchmark
        if found:  # If there was a benchmark found.
            return make_response(jsonify(found), 200)
        else:  # if there was no found benchmark for that product, then return "No benchmark found"
            return make_response(jsonify("No benchmark found."), 404)
    else:
        # If the payload doesn't pass payload check, return 400
        return make_response(jsonify(msg), 400)


# SEARCH BENCHMARKS FOR PRODUCT BY DATE
b_date_sample = {
    "product": ["str"],
    "date": ["str"]  # format 2020-12-06
}
"""
CURL-FRIENDLY TEST:
$ curl -d '{"product": "accumulator", "date": "2020-12-04"}' -H "Content-Type: application/json" -X POST http://localhost:5000/benchmarks/get/date
"""
@app.route("/benchmarks/get/date", methods=["POST"])
def benchmarks_date():
    query = request.get_json()  # Get query as json
    check, msg = check_payload(b_date_sample, query)  # Check payload

    if check:
        found = coll_benchmarks.find({'product': query["product"], 'date': query["date"]})  # find dated benchmarks
        li = list(found)
        if len(li) > 0:  # If there was at least one benchmark found.
            return make_response(jsonify(li), 200)
        else:  # if there were no found benchmarks for that product on that date, then return "No benchmarks found."
            return make_response(jsonify("No benchmarks found."), 404)
    else:
        # If the payload doesn't pass payload check, return 400
        return make_response(jsonify(msg), 400)


# SEARCH BENCHMARKS FOR PARENTS OF PRODUCT
b_parents_sample = {
    "product": ["str"],
    "search": ["str"]  # must be either "latest" or "all".
}
"""
CURL-FRIENDLY TEST:
$ curl -d '{"product": "accumulator", "search": "latest"}' -H "Content-Type: application/json" -X POST http://localhost:5000/benchmarks/get/parents
"""
@app.route("/benchmarks/get/parents", methods=["POST"])
def benchmarks_parents():
    query = request.get_json()  # Get query as json
    check, msg = check_payload(b_parents_sample, query)  # Check payload

    if check:
        if query["search"] == "latest":
            found = coll_benchmarks.find({ "sub_products.product": query["product"], "latest_benchmark": True })
            li = list(found)
            if len(li) > 0:  # If there was at least one benchmark found.
                return make_response(jsonify(li), 200)
            else:  # if there were no found benchmarks for that product on that date, then return "No benchmarks found."
                return make_response(jsonify("No benchmarks found."), 404)
        elif query["search"] == "all":
            found = coll_benchmarks.find({ "sub_products.product": query["product"] })  # find all parent benchmarks
            li = list(found)
            if len(li) > 0:  # If there was at least one benchmark found.
                return make_response(jsonify(li), 200)
            else:  # if there were no found benchmarks for that product on that date, then return "No benchmarks found."
                return make_response(jsonify("No benchmarks found."), 404)
        else:  # in case the request contains a strange value in key 'search'.
            s = f"Unexpected value '{query['search']}' in key 'search'. Should be either 'latest' or 'all'."
            return make_response(jsonify(s), 400)
    else:
        # If the payload doesn't pass payload check, return 400
        return make_response(jsonify(msg), 400)


# SEARCH BENCHMARKS FOR PRODUCT BY DATE
b_create_sample = {
    "product": ["str"],
    "kg_per_unit": ["int", "float"],
    "unit": ["str"],
    "self_impact": {
        "co2": ["int", "float"],
        "measurement_error": ["float"],
        "energy_sources": ["list:str"]
    },
    "sub_products": [
        {
            "product": ["str"],
            "unit_amount": ["int", "float"],
            "transport": ["int", "str"]
        }
    ]
}
"""
CURL-FRIENDLY TEST:
$ curl -d '{"product": "accumulator", "kg_per_unit": 2, "unit": "piece", "self_impact": { "co2": 0.15, "measurement_error": 0.02, "energy_sources": ["biogas"] }, "sub_products": [ { "product": "chs-märken", "unit_amount": 25, "transport": 69 }, { "product": "locomotive", "unit_amount": 1, "transport": 42 } ] }' -H "Content-Type: application/json" -X POST http://localhost:5000/benchmarks/create
"""
@app.route("/benchmarks/create", methods=["POST"])
def benchmarks_create():
    query = request.get_json()  # Get query as json
    check, msg = check_payload(b_create_sample, query)  # Check payload

    if check:
        # Make sure that the product you're making a new benchmark for actually exists.
        if not coll_products.find_one({"_id": query["product"]}):
            return make_response(jsonify(f"ERROR: No product with ID '{query['product']}' exists."), 404)

        benchmark = {
            "product": query["product"],
            "kg_per_unit": query["kg_per_unit"],
            "unit": query["unit"],
            "self_impact": {
                "co2": query["self_impact"]["co2"],
                "measurement_error": query["self_impact"]["measurement_error"],
                "energy_sources": [es.lower() for es in query["self_impact"]["energy_sources"]]
            },
            "sub_products": query["sub_products"],
        }
        b = add_benchmark(benchmark)
        return make_response(jsonify(b), 200)
    else:
        # If the payload doesn't pass payload check, return 400
        return make_response(jsonify(msg), 400)
