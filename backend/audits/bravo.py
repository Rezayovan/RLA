#!/usr/bin/python
# -*- coding: UTF-8 -*-

""" Ballot-polling audit in Python
A Python implementation of the BRAVO algorithm described in "BRAVO:
Ballot-polling Risk-limiting Audits to Verify Outcomes" (Lindeman,
Stark, and Yates 2012). The full paper can be found on usenix.org
<https://www.usenix.org/system/files/conference/evtwote12/evtwote12-final27.pdf>
"""

import numpy as np
from recordclass import recordclass
import threading
import random

Candidates = recordclass("Candidates", "winners losers")
Hypotheses = recordclass("Hypotheses", "test_stat reject_count")
Bravo_Params = recordclass("BPA_Inputs", "votes_array num_ballots num_winners risk_limit seed max_tests")

IS_DONE = False
IS_DONE_MESSAGE = ""

_BUFFER = []
_LOCK = threading.Lock()
_CV = threading.Condition(_LOCK)

# TODO: destroy any other running threads running an audit
# TODO: call this in app.py in the /perform_audit route
def reset_audit():
    global IS_DONE, IS_DONE_MESSAGE
    _BUFFER = []
    IS_DONE = False
    IS_DONE_MESSAGE = ""

def append_buffer(vote):
    _CV.acquire()
    global _BUFFER
    _BUFFER.append(vote)
    print(_BUFFER)
    _CV.notify()
    _CV.release()

def get_votes():
    # TODO: Send selected ballot to frontend for the user to input
    #       the ballot's actual votes.
    # TODO: Receive and return list of 'votes' (at most size
    #       `num_winners`) via API call where each `vote`,
    #       0 ≤ `vote` ≤ `num_candidates`.
    print("getting vote")
    _CV.acquire()
    global _BUFFER
    while not _BUFFER:
        print("wait condition")
        _CV.wait()
    votes = _BUFFER.pop(0)
    _CV.release()
    # votes is a list of integer lists
    # undervotes and overvotes are handled by bravo algo
    return votes


def arrange_candidates(votes_array, num_winners):
    """
    From `votes_array`, we can find the winners as the `num_winners` candidates
    (indices) with the most votes. The losers are the rest of the candidates.
    """
    sorted_candidates = sorted(enumerate(votes_array), key=lambda t: t[1], reverse=True)
    winners = set(t[0] for t in sorted_candidates[:num_winners])
    losers = set(t[0] for t in sorted_candidates[num_winners:])

    return Candidates(winners, losers)


def get_margins(votes_array, candidates, num_candidates):
    """
    Let `margins[winner][loser] ≡ VOTES[winner]/(VOTES[winner] + VOTES[loser])`
    be the fraction of votes `winner` was reported to have received among
    ballots reported to show a vote for `winner` or `loser` or both.
    """
    margins = np.zeros([num_candidates, num_candidates])
    for winner in candidates.winners:
        for loser in candidates.losers:
            margins[winner][loser] = votes_array[winner] \
                    / (votes_array[winner] + votes_array[loser])
    return margins


def get_sequence_number(num_ballots):
    """Returns random sequence number to draw ballot from."""
    ballot_to_draw = random.randint(1, num_ballots)
    return ballot_to_draw

def get_ballot(num_winners, num_ballots):
    """ Step 2 of the BRAVO algorithm.
    Randomly picks a ballot to test and returns a list of its votes.
    The ballot picked is returned to the frontend for the user to input
    actual votes on the ballot. The ballot should be selected using a
    random function seeded by a user-generated seed.
    Note: 'random' should be seeded before this function is called.
    """
    ballot_votes = [1]

    if len(ballot_votes) <= num_winners:
        return []
    return ballot_votes


def update_hypothesis(hypotheses, winner, loser, risk_limit):
    """ Step 5 of the BRAVO algorithm.
    Rejects the null hypothesis corresponding to the test statistic of
    the `winner` and `loser` pair. Increments the null hypothesis
    rejection count.
    """
    if hypotheses.test_stat[winner][loser] >= 1/risk_limit:
        hypotheses.test_stat[winner][loser] = 0
        hypotheses.reject_count += 1

def update_audit_stats(vote, candidates, hypotheses, margins, risk_limit):
    """ Steps 3-5 from the BRAVO algorithm.
    Updates the `test_statistic` and rejects the corresponding null
    hypothesis when appropriate.
    """
    print("Test stat first: ", self.hypotheses.test_stat)

    if vote in candidates.winners: # Step 3
        for loser in candidates.losers:
            hypotheses.test_stat[vote][loser] *= 2*margins[vote][loser]
            update_hypothesis(hypotheses, vote, loser, risk_limit)
    elif vote in candidates.losers: # Step 4
        for winner in candidates.winners:
            hypotheses.test_stat[winner][vote] *= 2*(1-margins[winner][vote])
            update_hypothesis(hypotheses, winner, vote, risk_limit)

    print("Test stat first: ", self.hypotheses.test_stat)


def run_audit(candidates, num_ballots, max_tests, margins, seed, risk_limit):
    """
    Runs the algorithm given in "BRAVO" (2012) §7.
    """
    num_winners = len(candidates.winners)
    num_losers = len(candidates.losers)
    num_candidates = num_winners + num_losers

    test_statistic = np.ones([num_candidates, num_candidates])
    reject_count = 0
    num_null_hypotheses = num_winners * num_losers
    hypotheses = Hypotheses(test_statistic, reject_count)

    ballots_tested = 0

    while ballots_tested < max_tests: # Step 6
        ballot_votes = get_ballot(num_winners, num_ballots)
        assert all(0 <= vote < num_candidates for vote in ballot_votes)
        for vote in ballot_votes:
            update_audit_stats(vote, candidates, hypotheses, margins, risk_limit)
        ballots_tested += 1
        print(ballots_tested)

        # Step 6
        if hypotheses.reject_count >= num_null_hypotheses:
            return True

    return False


def bravo(params):
    """BRAVO Ballot-Polling Audit Implementation
    Given an array of votes cast, the number of winners, a risk limit, and a
    maximum number of ballots to test, `bravo` runs an audit on the election
    results to confirm with `risk_limit` confidence that the reported
    `num_winners` winner(s) are indeed the winners.
    """
    print("params for bravo")
    print(params)
    num_candidates = len(params.votes_array)

    # Ensure parameters make sense
    assert 0 < params.num_winners <= num_candidates
    assert 0. < params.risk_limit <= 1.
    assert all(votes >= 0 for votes in params.votes_array)
    if params.max_tests <= 0:
        params.max_tests = sum(params.votes_array)
    else:
        params.max_tests = min(params.max_tests, sum(params.votes_array))

    random.seed(params.seed)
    candidates = arrange_candidates(params.votes_array, params.num_winners)
    margins = get_margins(params.votes_array, candidates, num_candidates)
    result = run_audit(candidates, params.num_ballots, params.max_tests, margins, params.seed, params.risk_limit)

    print(result)
    global IS_DONE, IS_DONE_MESSAGE
    if result:
        # print("Audit completed: the results stand.")
        IS_DONE = True
        IS_DONE_MESSAGE = "Audit completed: the results stand."
    else:
        # print("Too many ballots tested. Perform a full hand-recount of the ballots.")
        IS_DONE = True
        IS_DONE_MESSAGE = "Too many ballots tested. Perform a full hand-recount of the ballots."

def run_bravo(params):
    reset_audit()
    PARAMS = Bravo_Params(*params)
    bravo(PARAMS)

# def run_bravo_hardcode():
#     PARAMS = Bravo_Params(VOTES_ARR, TOTAL_VOTES, NUM_WINNERS, ALPHA, SEED, MAX_TESTS)
#     bravo(PARAMS)

if __name__ == "__main__":
    ##### DUMMY DATA ######
    VOTES_ARR = [0, 100]
    TOTAL_VOTES = sum(VOTES_ARR)
    NUM_WINNERS = 1
    ALPHA = .10
    MAX_TESTS = 10
    SEED = 1234567890
    ######################
    PARAMS = Bravo_Params(VOTES_ARR, TOTAL_VOTES, NUM_WINNERS, ALPHA, SEED, MAX_TESTS)
    bravo(PARAMS)
