import flaskr
import config

# All this server.py file does, is import the the flask API module flaskr, and run the API.
# This is mostly for making it easy to run when developing the API.
flaskr.app.run(debug=True, host=config.get_setting("host"), port=config.get_setting("port"))