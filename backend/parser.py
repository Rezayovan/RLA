from flask import Flask, request, jsonify
from flask_cors import CORS
from pathlib import Path
from werkzeug.utils import secure_filename
import json

from utilities.csv_parser import parse_election_data_csv
from utilities.helpers import delete_file, all_keys_present_in_dict

from BravoClass import Bravo

'''Returns audit object.'''

class Audit:
  def __init__(self):
    pass

def parse(request):
  form = request.form
  if 'audit-type' not in form:
    return "Audit type not specified.", 500

  audit_type = form['audit-type']
  if audit_type == "bravo":
    # create dictionary for BRAVO params
    form_params = ['candidate-name-vote-dict', 'num-ballots-cast', 'num-winners', 'risk-limit']
    if not all_keys_present_in_dict(form_params, form):
      return "Not all required BRAVO parameters were provided.", 500

    # Parse candidate name and vote JSON data
    candidate_data = json.loads(form['candidate-name-vote-dict'])
    num_ballots_cast = form['num-ballots-cast']
    num_winners = form['num-winners']
    risk_limit = form['risk-limit']
    # TODO get the MAX_TEST variable from frontend
    params = [[value for key,value in candidate_data.items()], int(num_winners), float(risk_limit) / 100, 10]
    return Bravo(params)
