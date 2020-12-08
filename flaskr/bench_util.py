import flask
from flask import request, jsonify, make_response
from flaskr import app, check_payload
from flaskr.db import coll_benchmarks, coll_transports
import datetime
import json

# Get chain impact for a specific product id using the latest benchmarks for that product.
def get_chain_impact(_id):
    # Get which product we are trying to find the chain impact for
    me = coll_benchmarks.find_one({"product": _id, "latest_benchmark": True})

    # If this product exists
    if me:
        # If the chain impact for this product hasn't been calculated
        if me["chain_impact"]["co2"] == 0:
            total_sub_products_co2 = 0

            # Loop through all sub products of this product
            for sub in me["sub_products"]:

                # Get how many of this sub product we are using
                amount = sub["unit_amount"]

                # Get that sub product's kg_per_unit and unit
                subby = coll_benchmarks.find_one({"product": sub["product"], "latest_benchmark": True}, {"kg_per_unit": 1, "unit": 1})
                if not subby:
                    subby = {
                        "unit": "UNDEFINED",
                        "kg_per_unit": 1
                    }

                # Create easier variables for kg_per_unit and unit
                unit = subby["unit"]
                kg_per_unit = subby["kg_per_unit"]

                # Recursively get the chain impact of this sub product
                sub_co2_per_unit = get_chain_impact(sub["product"])

                # Get which transport this sub product has been transported with
                trans = coll_transports.find_one({"_id": sub["transport"]}) 

                # Add the co2 emitted by the sub product times how many units of it is used
                total_sub_products_co2 += sub_co2_per_unit * amount

                # Add the co2 emitted by the transport
                total_sub_products_co2 += trans["impact"]["co2_per_kg_km"] * amount * kg_per_unit * trans["impact"]["distance_travelled"]

            #print(f"UPDATING {_id} with CO2: {round(me['self_impact']['co2'] + total_sub_products_co2, 3)}")
            
            # When we have summed all sub product's chain impacts, add our own self impact and then update the database with our new chain impact (also does this recursively)
            coll_benchmarks.update_one({"_id": me['_id'] }, { "$set": { "chain_impact.co2": round(me["self_impact"]["co2"] + total_sub_products_co2, 3) } })       

            # Also, since we might want the number in other places, return the chain impact co2 here.   
            return me["self_impact"]["co2"] + total_sub_products_co2

        # If we have already calculated the co2 chain impact, then just return it immediately.
        return me["chain_impact"]["co2"]

    # If the product does not exists, then return 0 co2.
    return 0

# Inserting a benchmark to the database, does not check if it already exists, so make sure to do that before.
def insert_benchmark(benchmark)
    # Insert benchmark to database
    coll_benchmarks.insert_one(benchmark)

    # Get the chain impact for the newly created benchmark
    co2 = get_chain_impact(benchmark["product"])

    # Update the newly created benchmark in the database
    coll_benchmarks.update_one({"_id": benchmark["_id"]}, {"$set": { "chain_impact.co2": co2 } } )
    
    return benchmark
    