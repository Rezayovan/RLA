from flask import Flask, request, jsonify
from flask_cors import CORS
from pathlib import Path
from werkzeug.utils import secure_filename
from threading import Thread
from secrets import token_urlsafe
import json

from utilities.csv_parser import parse_election_data_csv
from utilities.helpers import delete_file, all_keys_present_in_dict, get_vw_and_vl

from audits.Bravo import Bravo
from audits.Cast import Cast
from audits.SuperSimple import SuperSimple
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
    print(audit_type)
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
        random_seed = float(form_data['random_seed'])
        max_tests = int(form_data['max_tests'])

        # votes_array num_ballots num_winners risk_limit seed max_tests
        params_list = [candidate_data, num_ballots_cast, num_winners, risk_limit, random_seed, max_tests]
        bravo_object = Bravo(*params_list)
        bravo_thread = Thread(target=bravo_object.bravo)
        bravo_thread.start()

        # get sample size
        estimated_sample_size = bravo_object.get_sample_size()

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
    elif audit_type == 'super_simple':
        form_params = ['candidate_votes', 'num_ballots_cast', 'num_winners', 'risk_limit', 'inflation_rate', 'tolerance', 'random_seed']
        if not all_keys_present_in_dict(form_params, form_data):
            return 'Not all required super-simple parameters were provided.', 500

        # Parse candidate name and vote JSON data
        candidate_data_json = json.loads(form_data['candidate_votes'])
        candidate_data = [int(val) for val in candidate_data_json]
        num_ballots_cast = int(form_data['num_ballots_cast'])
        num_winners = int(form_data['num_winners'])
        risk_limit = float(form_data['risk_limit']) / 100
        inflation_rate = float(form_data['inflation_rate']) / 100
        tolerance = float(form_data['tolerance']) / 100
        random_seed = int(form_data['random_seed'])
        max_tests = int(form_data['max_tests'])

        # votes_array, num_ballots, num_winners, risk_limit, seed, inflation_rate, tolerance
        params_list = [candidate_data, num_ballots_cast, num_winners, risk_limit, random_seed,  inflation_rate, tolerance]
        ss_obj = SuperSimple(*params_list)
        sample_size = ss_obj.sample_size()
        session_id = token_urlsafe(32)
        CURRENT_RUNNING_AUDITS[session_id] = cast_object
        ss_thread = Thread(target=ss_obj.run_audit)
        ss_thread.start()
        first_sequence = cast_object.get_sequence_number()
        res = {
            'sequence_number_to_draw': first_sequence,
            'session_id': session_id,
            'estimated_sample_size': sample_size
        }
        return jsonify(res)
    elif audit_type == 'cast':
        form_params = ['initial_cvr_data',
                        'num_winners',
                        'risk_limit',
                        'random_seed',
                        'threshold',
                        'batch_size',
                        'num_batches',
                        'num_stages',
                        'num_candidates']
        if not all_keys_present_in_dict(form_params, form_data):
            return 'Not all required CAST parameters were provided.', 500

        # Parse candidate name and vote JSON data
        initial_cvr_data = json.loads(form_data['initial_cvr_data'])
        print(initial_cvr_data)
        print(initial_cvr_data)
        num_winners = int(form_data['num_winners'])
        risk_limit = float(form_data['risk_limit']) / 100
        random_seed = int(form_data['random_seed'])
        threshold = float(form_data['threshold']) / 100
        batch_size = int(form_data['batch_size'])
        num_batches = int(form_data['num_batches'])
        num_stages = int(form_data['num_stages'])
        num_candidates = int(form_data['num_candidates'])
        params_list = [initial_cvr_data, num_candidates, num_winners, num_stages, batch_size, num_batches, risk_limit, threshold, random_seed]

        cast_object = Cast(*params_list)
        cast_thread = Thread(target=cast_object.run_audit)
        cast_thread.start()

        session_id = token_urlsafe(32)
        CURRENT_RUNNING_AUDITS[session_id] = cast_object

        first_sequence = cast_object.get_sequence_number()
        res = {
            'sequence_number_to_draw': first_sequence,
            'session_id': session_id
        }
        return jsonify(res)
    elif audit_type == 'negexp':
        pass
    else:
        return f'{audit_type} is an invalid audit type!', 500

@app.route('/send_ballot_votes', methods=['POST'])
def send_ballot_votes():
    global CURRENT_RUNNING_AUDITS
    form_data = request.form

    if 'audit_type' not in form_data:
        return 'Audit type not specified.', 500

    if 'session_id' not in form_data:
        return 'Session ID not specified. Unable to retrieve audit status.', 500

    session_id = form_data['session_id']
    audit_type = form_data['audit_type']

    if audit_type == 'bravo':
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
    elif audit_type == 'super_simple':
        form_params = ['latest_ballot_votes', 'num_ballots_cast']
        if not all_keys_present_in_dict(form_params, form_data):
            return 'Not all required BRAVO parameters were provided.', 500

        ballot_votes_json = json.loads(form_data['latest_ballot_votes'])
        ballot_votes_list = [int(vote) for vote in ballot_votes_json]
        cvr_votes_json = json.loads(form_data['latest_cvr_votes'])
        cvr_votes_list = [int(vote) for vote in cvr_votes_json]

        return "YOO SUPER SIMPLE!", 200
        # TODO: finish
    elif audit_type == 'cast':
        cast = CURRENT_RUNNING_AUDITS[session_id]
        if cast.IS_DONE:
            # return status code 204
            return 'Cast audit complete!', 204

        form_params = ['batch_votes']
        if not all_keys_present_in_dict(form_params, form_data):
            print("error 500")
            return 'Not all required CAST parameters were provided.', 500

        batch = form_data['batch_votes']
        cast.append_votes_buffer(batch)

        sequence = cast.get_sequence_number()
        res = {'sequence_number_to_draw': sequence}
        return jsonify(res)
    elif audit_type == 'negexp':
        pass
    else:
        return f'{audit_type} is an invalid audit type!', 500



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
        'completion_message': current_audit.IS_DONE_MESSAGE,
        'flag': current_audit.IS_DONE_FLAG
    }
    return jsonify(res)

@app.route('/end_audit', methods=['POST'])
def end_audit():
    form_data = request.form

    if 'session_id' not in form_data:
        return 'Session ID not specified. Unable to retrieve audit status.', 500

    session_id = form_data['session_id']

    global CURRENT_RUNNING_AUDITS
    if session_id in CURRENT_RUNNING_AUDITS:
        CURRENT_RUNNING_AUDITS.pop(session_id, None)

    return "Successfully ended audit session and revoked session ID.", 200

@app.route('/get_sample_sizes_for_open_election_data', methods=['POST'])
def get_sample_sizes():
    if 'election-data-spreadsheet' not in request.files:
        'OpenElection data not uploaded.', 500

    form_data = request.form
    num_winners = int(form_data['num_winners'])
    file_data = request.files['election-data-spreadsheet']

    # Check if file is valid and if the extension is allowed
    # if file_data and allowed_file(file_data.filename):
    if file_data:
        filename = secure_filename(file_data.filename)
        data_path = str(Path(app.config['UPLOAD_FOLDER']).joinpath(filename))

        v_w = 0
        v_l = 0
        total_votes = 0

        try:
            file_data.save(data_path)

            # TODO: need some way to determine if we are processing OpenElection data and not a random CSV
            vote_dict, total_votes, office = parse_election_data_csv(data_path)

            # Convert dictionary of candidate/num_votes to list of num_votes
            votes_array = []
            for value in vote_dict.values():
                votes_array.append(value)

            v_w, v_l = get_vw_and_vl(votes_array, num_winners)
        except Exception as e:
            # Delete saved CSV on error
            delete_file(data_path)
            print(e)
            return "An error occurred while parsing the OpenElection data.", 500

        res = {
            'v_w': v_w,
            'v_l': v_l,
            'total_votes': total_votes,
            'office_chosen': office
        }

        # Delete saved CSV
        delete_file(data_path)
        return jsonify(res)
    else:
        return 'Invalid file uploaded. Please upload a spreadsheet in CSV format.', 500

def allowed_file(filename):
    return '.' in filename and Path(filename).suffix.lower() == 'csv'

if __name__ == '__main__':
    app.run()
