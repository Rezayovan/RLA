from flask import Flask, request, jsonify
from flask_cors import CORS
from pathlib import Path
from werkzeug.utils import secure_filename
import json

from utilities.csv_parser import parse_election_data_csv
from utilities.helpers import delete_file, all_keys_present_in_dict

from parser import parse

from bravo import run_bravo

app = Flask(__name__)

# Stretch goal: add support for XLS files
# ALLOWED_EXTENSIONS = set(['.xlsx', '.xls', '.csv'])

app.config.update(
    ENV='development',
    DEBUG=True,
    # Temporary save location. Required to parse uploaded
    # data since the incoming file is a stream
    UPLOAD_FOLDER=f'{Path.cwd()}/tmp_uploads'
)

'''
Needed to prevent CORS warnings in browser.

If we deploy this app for actual use, we should look into fixing the CORS issues
properly rather than using a workaround. CORS provides nice security perks.
'''
CORS(app)

'''
BRAVO form fields:
candidate-name-vote-dict: JSON
num-ballots-cast: int
num-winners: int
risk-limit: int
'''

@app.route('/perform_audit', methods=['POST'])
def perform_audit():
    """Will determine audit method and call run on that method."""
    params = parse(request)
    run_bravo(params)
    return status

@app.route('/vote_pick', methods=['POST'])
def vote_picked():
    """Sends picked vote to bravo app."""
    

@app.route('/upload_open_election_data', methods=['POST'])
def upload_open_election_data():
    # Determine type of audit
    # Determine input type (e.g. CSV vs form input)

    # User submitted OpenElection data
    if 'election-data-spreadsheet' in request.files:
        file_data = request.files['election-data-spreadsheet']
        # Check if file is valid and if the extension is allowed
        if file_data and allowed_file(file_data.filename):
            filename = secure_filename(file_data.filename)
            data_path = str(Path(app.config['UPLOAD_FOLDER']).joinpath(filename))

            try:
                file_data.save(data_path)
                # TODO: need some way to determine if we are processing OpenElection data and not a random CSV
                res = parse_election_data_csv(data_path, 'State House')
            except Exception as e:
                # Delete saved CSV on error
                delete_file(data_path)
                raise e

            # Delete saved CSV
            delete_file(data_path)
            return jsonify(res)
        else:
            return f'Invalid file uploaded. Please upload a spreadsheet in CSV format.', 500

    return 'Hello world!'

def allowed_file(filename):
    return '.' in filename and Path(filename).suffix.lower() == 'csv'

if __name__ == '__main__':
    app.run()
