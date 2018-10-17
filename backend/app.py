from flask import Flask
app = Flask(__name__)

"""This is the main controller.
    Need to figure out how to divide this"""

@app.route('/')
def hello_world():
    return 'Hello, World!'

@app.route('/test', methods=['POST'])
def post():
    return 'posts'


