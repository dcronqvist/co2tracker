from flask import Flask, make_response, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

# Below is a standard testing one
# This line specifies at which url you reach this defined method. Also which HTTP methods that can be used with it.
@app.route('/', methods=["GET"])
def hello_world(): # The method that is called when accessing the base url /
    # make_response creates a response with status code and correct headers.
    # jsonify turns the string "Hello World!" into a json-string.
    # We give the make_response method a json-string, and a status code, in this case 200 OK.
    # This response with then be passed to the below method (done automatically by Flask).
    # Look at comments on below method to understand.
    return make_response(jsonify("Hello World!"), 200) 

# Send the response in an appropriate format
# app.after_request is called whenever we return anything to the caller of the API.
# the response object is the response that make_response returns in all endpoints.
@app.after_request
def after(response):
    # Here we define a static structure for ALL responses by the API.
    # By doing this, we can make sure that all responses are in the same format
    # and all contain the status code of the response.
	ret = {
		"status_code": response.status_code, # 200
		"status": response.status, # 200 OK
		"response": response.get_json() # json-object
	}
    # creates the response and returns to the caller.
	return make_response(jsonify(ret), ret["status_code"])

def check_payload(sample, payload):
    """
    Loop through all keys in sample, make sure they all exist in the payload.
    Type check all keys to make sure they match. Lists are harder, since 
    there isn't an implementation to check if the elements are of the correct type.
    """
    # Loop through all keys in sample
    for key in sample:

        # Make sure that the payload has every single key that the sample does.
        if key in payload:

            # If the type in the sample is a list, then we have further checking to do.
            if type(sample[key]) == list:

                # If we have specified the first element in the list to be of 'list:<type>' format, then make 
                # sure that all elements in the payload on that key is of the type <type>.
                if "list:" in sample[key][0]:
                    # Split list specifyer on :, to retrieve which type that is allowed inside.
                    sp = sample[key][0].split(":")

                    # Type check all elements in the payload against the specified type in the sample
                    checked = [(type(ele) == eval(sp[1]), ele) for ele in payload[key]]

                    # Get which of the elements in the list that do not satisfy the type check.
                    checked = [e for ch, e in checked if not ch]

                    # If there were any elements that failed the type check, return ERROR: type check failed.
                    if len(checked) > 0:
                        ele = checked.pop()
                        return False, f"ERROR: On key '{key}', expected element type(s) '{eval(sp[1])}', got {type(ele)} at element {ele}."
                    # If no elements failed the type check, just keep looping through all keys.
                    else:
                        continue


                # If the sample value at the key is a list of strings, and weren't list specifiers ^ above case.
                if type(sample[key][0]) == str:

                    # Get all types which are OK for this key from the sample
                    ok_types = [eval(t) for t in sample[key]]

                    # If the payload's type is not in the OK types list, then return ERROR: failed type check.
                    if not (type(payload[key]) in ok_types):
                        return False, f"ERROR: On key '{key}', expected type(s) '{ok_types}', got '{type(payload[key])}'"


                # This case is if the sample at the key contains a list of objects
                elif type(sample[key][0]) == dict:
                    
                    # Type check all objects in the list of objects in the payload.
                    elements_check = [check_payload(sample[key][0], obj) for obj in payload[key]]

                    # Get all objects that failed the type check
                    failed_payloads = [msg for (succ, msg) in elements_check if not succ]

                    # If the length of failed_payloads is more than 0, then there is at least one that failed.
                    if len(failed_payloads) > 0: 
                        return False, failed_payloads.pop()
                    else:
                        continue
            elif type(sample[key]) == str:
                # If it is a string, then that means that the key must match EXACT
                if not (sample[key] == payload[key]):
                    return False, f"ERROR: On key '{key}', expected '{ok_types}', got '{payload[key]}'."
            else:
                # the sample is an object, recurse down
                succ, msg = check_payload(sample[key], payload[key])
                if not succ:
                    return succ, msg
        else:
            return False, f"ERROR: Missing key '{key}'"
    return True, "Payload matches sample."

# Here we will import endpoints
import flaskr.products
import flaskr.benchmarks
import flaskr.transports
