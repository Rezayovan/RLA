from flask import Flask
app = Flask(__name__)

@app.route('/send_data', methods=['POST'])
def send_data():
    # Determine type of audit
    
    # Determine input type (e.g. CSV vs form input)


if __name__ == '__main__':
    app.run()
