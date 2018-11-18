from flask import Flask, request, jsonify
from flask_cors import CORS
from pathlib import Path
from werkzeug.utils import secure_filename
import json

from utilities.csv_parser import parse_election_data_csv
from utilities.helpers import delete_file, all_keys_present_in_dict

from bravo import run_bravo
from bravo import run_bravo_hardcode
from bravo import append_buffer
from bravo import get_sequence_number

from threading import Thread

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
    # thread = Thread(target=run_bravo_hardcode)
    # thread.start()
    form_data = request.form
    if 'audit-type' not in form_data:
        return 'Audit type not specified.', 500

    audit_type = form_data['audit-type']

    # Perform BRAVO audit
    if audit_type == 'bravo':
        form_params = ['candidate-votes', 'num-ballots-cast', 'num-winners', 'risk-limit']
        if not all_keys_present_in_dict(form_params, form_data):
            return 'Not all required BRAVO parameters were provided.', 500

        # Parse candidate name and vote JSON data

        candidate_data = json.loads(form_data['candidate-votes'])
        num_ballots_cast = form_data['num-ballots-cast']
        num_winners = form_data['num-winners']
        risk_limit = float(form_data['risk-limit']) / 100
        seed = 12345
        candidate_data = [int(data) for data in candidate_data]
        params_list = [candidate_data,  int(num_ballots_cast), int(num_winners), risk_limit, seed, 20]
        run_bravo(params_list)

        return jsonify([candidate_data, num_ballots_cast, num_winners, risk_limit, seed, 20])

        # CALL BRAVO FUNCTION IN AUDITS FOLDER

    return 'audit request!'

@app.route('/get_sequence_number', methods=['POST'])
def get_seq_number():
    form_data = request.form
    num_ballots = int(form_data['num-ballots-cast'])
    num = get_sequence_number(num_ballots)
    return str(num)


@app.route("/receive_ballot", methods=['POST'])
def receive_ballot():
    form = request.form
    append_buffer(int(form["vote"]))
    return "received ballot"

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
