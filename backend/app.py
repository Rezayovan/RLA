from flask import Flask, request, jsonify
from flask_cors import CORS
from pathlib import Path
from werkzeug.utils import secure_filename
from threading import Thread
import json

from utilities.csv_parser import parse_election_data_csv
from utilities.helpers import delete_file, all_keys_present_in_dict

from audits import bravo

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

# TODO: NEED TO RESET DATA BETEWEEN CALLS TO THIS FUNCTION
@app.route('/perform_audit', methods=['POST'])
def perform_audit():
    form_data = request.form
    if 'audit-type' not in form_data:
        return 'Audit type not specified.', 500

    audit_type = form_data['audit-type']

    # Perform BRAVO audit
    if audit_type == 'bravo':
        form_params = ['candidate-votes', 'num-ballots-cast', 'num-winners', 'risk-limit', 'random-seed']
        if not all_keys_present_in_dict(form_params, form_data):
            return 'Not all required BRAVO parameters were provided.', 500

        # Parse candidate name and vote JSON data
        candidate_data_json = json.loads(form_data['candidate-votes'])
        candidate_data = [int(val) for val in candidate_data_json]
        num_ballots_cast = int(form_data['num-ballots-cast'])
        num_winners = int(form_data['num-winners'])
        risk_limit = float(form_data['risk-limit']) / 100
        random_seed = int(form_data['random-seed'])
        # max_tests = int(form_data['max-tests'])
        max_tests = 20

        # votes_array num_ballots num_winners risk_limit seed max_tests
        params_list = [candidate_data, num_ballots_cast, num_winners, risk_limit, random_seed, max_tests]
        bravo_thread = Thread(target=bravo.run_bravo, args=[params_list])
        bravo_thread.start()
        first_sequence = bravo.get_sequence_number(num_ballots_cast)
        return jsonify({"sequence_number_to_draw": first_sequence})

    return 'perform_audit() encountered an error!', 500

@app.route("/send_ballot_votes", methods=['POST'])
def send_ballot_votes():
    form_data = request.form
    if 'audit-type' not in form_data:
        return 'Audit type not specified.', 500

    audit_type = form_data['audit-type']

    if audit_type == 'bravo':
        if bravo.IS_DONE:
            # return status code 204
            return "BRAVO audit complete!", 204

        form_params = ['latest-ballot-votes', 'num-ballots-cast']
        if not all_keys_present_in_dict(form_params, form_data):
            return 'Not all required BRAVO parameters were provided.', 500

        ballot_votes_json = json.loads(form_data['latest-ballot-votes'])
        ballot_votes_list = [int(vote) for vote in ballot_votes_json]
        bravo.append_buffer(ballot_votes_list)

        num_ballots = int(form_data['num-ballots-cast'])
        sequence = bravo.get_sequence_number(num_ballots)
        return jsonify({"sequence_number_to_draw": sequence})

    return 'send_ballot_votes() encountered an error!', 500

@app.route("/get_audit_status", methods=['GET'])
def get_audit_status():
    # TODO: add this to support multiple users
    # session_id = request.form["session_id"]
    res = {
        "audit_complete": bravo.IS_DONE,
        "completion_message": bravo.IS_DONE_MESSAGE
    }
    return jsonify(res)

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
