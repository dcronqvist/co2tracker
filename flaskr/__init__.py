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

# Here we will import endpoints
import flaskr.products
