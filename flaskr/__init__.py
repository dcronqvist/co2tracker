from flask import Flask, make_response, jsonify

app = Flask(__name__)

# Here we will import endpoints
import flaskr.api


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