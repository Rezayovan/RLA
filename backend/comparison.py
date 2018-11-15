#!/usr/bin/python
# -*- coding: UTF-8 -*-

""" Ballot-comparison audit in Python
As described in "Super Simple Ballot Comparison Audits"
"""

from math import log
from recordclass import recordclass
from bravo import arrange_candidates, get_margins

Candidates = recordclass("Candidates", "winners losers")
Comparison_Params = recordclass("BCA_Inputs", "votes_array num_ballots num_winners risk_limit inflation_rate tolerance seed max_tests")

def super_simple(params):
    """ 'Super Simple' Ballot-comparison Audit Implementation
    """
    num_candidates = len(params.votes_array)

    # Ensure parameters make sense
    assert 0 < params.num_winners <= num_candidates
    assert 0. < params.risk_limit <= 1.
    assert all(votes >= 0 for votes in params.votes_array)
    if params.max_tests <= 0:
        params.max_tests = sum(params.votes_array)
    else:
        params.max_tests = min(params.max_tests, sum(params.votes_array))

    candidates = arrange_candidates(params.votes_array, params.num_winners)
    margins = get_margins(params.votes_array, candidates, num_candidates)
    multiplier = (params.tolerance * log(1 - 1/(2 * params.inflation_rate))) \
                    - (2 * log(params.risk_limit) * params.inflation_rate)
    # TODO: Draw (multiplier/margin) ballots at random and audit
