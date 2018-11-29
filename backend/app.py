from flask import Flask, request, jsonify
from flask_cors import CORS
from pathlib import Path
from werkzeug.utils import secure_filename
from threading import Thread
from secrets import token_urlsafe
import json

from utilities.csv_parser import parse_election_data_csv
from utilities.helpers import delete_file, all_keys_present_in_dict

from audits.Bravo import Bravo

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
Tracks current running audits
Key: session_id
Value: Audit object with a running thread
'''
CURRENT_RUNNING_AUDITS = {}

@app.route('/perform_audit', methods=['POST'])
def perform_audit():
    form_data = request.form
    if 'audit_type' not in form_data:
        return 'Audit type not specified.', 500

    audit_type = form_data['audit_type']

    # Perform BRAVO audit
    if audit_type == 'bravo':
        form_params = ['candidate_votes', 'num_ballots_cast', 'num_winners', 'risk_limit', 'random_seed']
        if not all_keys_present_in_dict(form_params, form_data):
            return 'Not all required BRAVO parameters were provided.', 500

        # Parse candidate name and vote JSON data
        candidate_data_json = json.loads(form_data['candidate_votes'])
        candidate_data = [int(val) for val in candidate_data_json]
        num_ballots_cast = int(form_data['num_ballots_cast'])
        num_winners = int(form_data['num_winners'])
        risk_limit = float(form_data['risk_limit']) / 100
        random_seed = int(form_data['random_seed'])
        max_tests = int(form_data['max_tests'])

        # votes_array num_ballots num_winners risk_limit seed max_tests
        params_list = [candidate_data, num_ballots_cast, num_winners, risk_limit, random_seed, max_tests]
        bravo_object = Bravo(*params_list)
        bravo_thread = Thread(target=bravo_object.bravo)
        bravo_thread.start()

        # get sample size

        estimated_sample_size = 0
        try:
            estimated_sample_size = bravo_object.get_sample_size()
        except ValueError as e:
            print("Sample size could not be calculated due to an error:", e)

        # Save object to retrieve audit status for a particular user
        # in subsequent requests
        session_id = token_urlsafe(32)
        global CURRENT_RUNNING_AUDITS
        CURRENT_RUNNING_AUDITS[session_id] = bravo_object

        first_sequence = bravo_object.get_sequence_number()
        res = {
            'sequence_number_to_draw': first_sequence,
            'estimated_sample_size': estimated_sample_size,
            'session_id': session_id
        }
        return jsonify(res)

    return 'perform_audit() encountered an error!', 500

@app.route('/send_ballot_votes', methods=['POST'])
def send_ballot_votes():
    form_data = request.form

    if 'audit_type' not in form_data:
        return 'Audit type not specified.', 500

    if 'session_id' not in form_data:
        return 'Session ID not specified. Unable to retrieve audit status.', 500

    session_id = form_data['session_id']
    audit_type = form_data['audit_type']

    if audit_type == 'bravo':
        global CURRENT_RUNNING_AUDITS
        bravo = CURRENT_RUNNING_AUDITS[session_id]
        if bravo.IS_DONE:
            # return status code 204
            return 'BRAVO audit complete!', 204

        form_params = ['latest_ballot_votes', 'num_ballots_cast']
        if not all_keys_present_in_dict(form_params, form_data):
            return 'Not all required BRAVO parameters were provided.', 500

        ballot_votes_json = json.loads(form_data['latest_ballot_votes'])
        ballot_votes_list = [int(vote) for vote in ballot_votes_json]
        bravo.append_votes_buffer(ballot_votes_list)

        sequence = bravo.get_sequence_number()
        res = {'sequence_number_to_draw': sequence}
        return jsonify(res)

    return 'send_ballot_votes() encountered an error!', 500

@app.route('/check_audit_status', methods=['POST'])
def check_audit_status():
    form_data = request.form

    if 'session_id' not in form_data:
        return 'Session ID not specified. Unable to retrieve audit status.', 500

    session_id = form_data['session_id']

    global CURRENT_RUNNING_AUDITS
    if session_id not in CURRENT_RUNNING_AUDITS:
        return f'Session ID invalid. No running audit can be found for th session ID: {session_id}.', 500
    current_audit = CURRENT_RUNNING_AUDITS[session_id]

    # Remove the current running audit from the CURRENT_RUNNING_AUDITS dict
    if current_audit.IS_DONE:
        CURRENT_RUNNING_AUDITS.pop(session_id, None)

    res = {
        'audit_complete': current_audit.IS_DONE,
        'completion_message': current_audit.IS_DONE_MESSAGE
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
