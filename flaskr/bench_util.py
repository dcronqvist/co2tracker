import flask
from flask import request, jsonify, make_response
from flaskr import app, check_payload
from flaskr.db import coll_benchmarks, coll_transports
import datetime
import json
from datetime import datetime as dt


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
                subby = coll_benchmarks.find_one({ "product": sub["product"], "latest_benchmark": True }, {"kg_per_unit": 1 })
                if not subby:
                    subby = {
                        "kg_per_unit": 1
                    }

                # Create easier variables for kg_per_unit and unit
                kg_per_unit = subby["kg_per_unit"]

                # Recursively get the chain impact of this sub product
                sub_co2_per_unit = get_chain_impact(sub["product"])

                # Get which transport this sub product has been transported with
                trans = coll_transports.find_one({"_id": sub["transport"]})

                # Add the co2 emitted by the sub product times how many units of it is used
                total_sub_products_co2 += sub_co2_per_unit * amount

                # Add the co2 emitted by the transport
                trans_co2 = trans["impact"]["co2_per_kg_km"] * amount * kg_per_unit * trans["impact"]["distance_travelled"]
                total_sub_products_co2 += trans_co2

            # When we have summed all sub product's chain impacts, add our own self impact and then update the database
            # with our new chain impact (also does this recursively)
            new_co2 = round(me["self_impact"]["co2"] + total_sub_products_co2, 3)
            coll_benchmarks.update_one({"_id": me['_id'] }, { "$set": { "chain_impact.co2": new_co2 } })

            # Also, since we might want the number in other places, return the chain impact co2 here.
            return me["self_impact"]["co2"] + total_sub_products_co2

        # If we have already calculated the co2 chain impact, then just return it immediately.
        return me["chain_impact"]["co2"]

    # If the product does not exists, then return 0 co2.
    return 0


# Create a chain impact for the specified benchmark by looping through all sub products.
def create_chain_impact(benchmark):
    # Start off with a chain impact that's completely empty
    chain = {
        "co2": 0,
        "measurement_error": 0
    }
    total_sub_products_co2 = 0

    # Loop through all sub products
    for sub in benchmark["sub_products"]:
        # Get how many of this sub product that we are using
        amount = sub["unit_amount"]

        # Find the sub product's latest benchmark in the database
        subby = coll_benchmarks.find_one({"product": sub["product"], "latest_benchmark": True}, {"kg_per_unit": 1})

        # If we couldn't find one, then we set the kg_per_unit to a standard value of 1 kg per unit
        if not subby:
            subby = {
                "kg_per_unit": 1
            }

        # Get the kg_per_unit from the looked up sub product
        kg_per_unit = subby["kg_per_unit"]

        # Start calculating the chain impact of the sub product - this is probably already done, so it's fast
        sub_co2_per_unit = get_chain_impact(sub["product"])

        # Get info about the transport that was used for this sub product
        trans = coll_transports.find_one({"_id": sub["transport"]})

        # Add the co2 per unit from the sub product's chain impact and multiply by how many we are using
        total_sub_products_co2 += sub_co2_per_unit * amount

        # Then add the amount of co2 emitted by the transport
        total_sub_products_co2 += trans["impact"]["co2_per_kg_km"] * amount * kg_per_unit * trans["impact"]["distance_travelled"]

    # Set the co2 in the chain impact to a float with at most 3 decimal points.
    chain["co2"] = round(benchmark["self_impact"]["co2"] + total_sub_products_co2, 3)
    return chain


# Inserting a benchmark to the database, does not check if it already exists, so make sure to do that before.
def insert_benchmark(benchmark):
    # Insert benchmark to database
    coll_benchmarks.insert_one(benchmark)

    # Get the chain impact for the newly created benchmark
    co2 = get_chain_impact(benchmark["product"])

    # Update the newly created benchmark in the database
    coll_benchmarks.update_one({"_id": benchmark["_id"]}, {"$set": { "chain_impact.co2": co2 } } )
    return benchmark


def add_benchmark(benchmark):
    # We start by creating the chain impact from the specified benchmark without inserting or updating the database
    chain = create_chain_impact(benchmark)

    # Set necessary fields
    benchmark["date"] = dt.today().strftime("%Y-%m-%d")
    benchmark["_id"] = benchmark["product"] + "-" + dt.today().strftime("%Y-%m-%d") + "-" + dt.now().strftime("%H:%M:%S")
    benchmark["chain_impact"] = chain
    benchmark["latest_benchmark"] = True

    # Update the old "latest one" to not be latest anymore
    coll_benchmarks.update_one({"product": benchmark["product"], "latest_benchmark": True }, { "$set": { "latest_benchmark": False } })
    # Insert the new "latest one".
    coll_benchmarks.insert_one(benchmark)

    # Lookup all parents of this product and turn it into an iterable list
    f = coll_benchmarks.find({ "sub_products.product": benchmark["product"], "latest_benchmark": True })
    parents = list(f)

    # Loop through all parents
    for parent in parents:
        # Update this parent to no longer be the latest version of itself
        coll_benchmarks.update_one({"_id": parent["_id"]}, { "$set": { "latest_benchmark": False } })

        # Create the new benchmark for this parent
        p_benchmark = {
            "date": dt.now().strftime("%Y-%m-%d-") + dt.now().strftime("%H:%M:%S"),
            "_id": parent["product"] + "-" + dt.now().strftime("%Y-%m-%d-") + dt.now().strftime("%H:%M:%S"),
            "product": parent["product"],
            "kg_per_unit": parent["kg_per_unit"],
            "unit": parent["unit"],
            "self_impact": parent["self_impact"],
            "sub_products": parent["sub_products"],
            "latest_benchmark": True
        }

        # Then recursively add, so we make sure that we update this parent's parents.
        add_benchmark(p_benchmark)
    return benchmark
