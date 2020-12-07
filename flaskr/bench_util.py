import flask
from flask import request, jsonify, make_response
from flaskr import app, check_payload
from flaskr.db import coll_benchmarks, coll_transports
import datetime
import json

def get_chain_impact(_id):
    me = coll_benchmarks.find_one({"product": _id, "latest_benchmark": True})

    if me:
        if me["chain_impact"]["co2"] == 0:
            total_sub_products_co2 = 0
            for sub in me["sub_products"]:
                amount = sub["unit_amount"]

                subby = coll_benchmarks.find_one({"product": sub["product"], "latest_benchmark": True}, {"kg_per_unit": 1, "unit": 1})
                if not subby:
                    subby = {
                        "unit": "UNDEFINED",
                        "kg_per_unit": 1
                    }

                unit = subby["unit"]
                kg_per_unit = subby["kg_per_unit"]
                sub_co2_per_unit = get_chain_impact(sub["product"])
                trans = coll_transports.find_one({"_id": sub["transport"]}) 
                total_sub_products_co2 += sub_co2_per_unit * amount
                total_sub_products_co2 += trans["impact"]["co2_per_kg_km"] * amount * kg_per_unit * trans["impact"]["distance_travelled"]
            print(f"UPDATING {_id} with CO2: {round(me['self_impact']['co2'] + total_sub_products_co2, 3)}")
            coll_benchmarks.update_one({"_id": me['_id'] }, { "$set": { "chain_impact.co2": round(me["self_impact"]["co2"] + total_sub_products_co2, 3) } })          
            return me["self_impact"]["co2"] + total_sub_products_co2
        return me["chain_impact"]["co2"]
    return 0

def insert_benchmark(benchmark):
    coll_benchmarks.insert_one(benchmark)
    co2 = get_chain_impact(benchmark["product"])
    coll_benchmarks.update_one({"_id": benchmark["_id"]}, {"$set": { "chain_impact.co2": co2 } } )
    return benchmark
    