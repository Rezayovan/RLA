""" Ballot-polling audit in Python
A Python implementation of the BRAVO algorithm described in "BRAVO:
Ballot-polling Risk-limiting Audits to Verify Outcomes" (Lindeman,
Stark, and Yates 2012). The full paper can be found on usenix.org
<https://www.usenix.org/system/files/conference/evtwote12/evtwote12-final27.pdf>
"""

import numpy as np
from recordclass import recordclass

Candidates = recordclass("Candidates", "winners losers")
Hypotheses = recordclass("Hypotheses", "test_stat reject_count")

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


def get_ballot(num_winners):
    """ Step 2 of the BRAVO algorithm.
    Randomly picks a ballot to test and returns a list of its votes.
    The ballot picked is returned to the frontend for the user to input
    actual votes on the ballot. The ballot should be selected using a
    random function seeded by a user-generated seed.
    """
    # TODO: Use the seed to pick a ballot at random.
    # TODO: Send selected ballot to frontend for the user to input
    #       the ballot's actual votes.
    # TODO: Receive list of 'votes' (at most size `num_winners`) via API call
    #       where each `vote`, 0 ≤ `vote` ≤ `num_candidates`.
    ballot_votes = [] # size in [0, w)
    # TODO: Delete following loop when API calls are made.
    for _ in range(num_winners):
        ballot_votes.append(5)

    return ballot_votes


def check_reject_hypothesis(test_statistic, reject_count, risk_limit):
    """ Step 5 of the BRAVO algorithm.
    Rejects the null hypothesis corresponding to the test statistic of
    the `winner` and `loser` pair. Increments the null hypothesis
    rejection count.
    """
    if test_statistic >= (1/risk_limit):
        test_statistic = 0
        reject_count += 1

def update_audit_stats(vote, candidates, hypotheses, margins, risk_limit):
    """ Steps 3-5 from the BRAVO algorithm.
    Updates the `test_statistic` and rejects the corresponding null
    hypothesis when appropriate.
    """
    if vote in candidates.winners: # Step 3
        for loser in candidates.losers:
            hypotheses.test_stat[vote][loser] *= (2*margins[vote][loser])
            check_reject_hypothesis(
                hypotheses.test_stat[vote][loser],
                hypotheses.reject_count, risk_limit)
    elif vote in candidates.losers: # Step 4
        for winner in candidates.winners:
            hypotheses.test_stat[winner][vote] *= (2*(1-margins[winner][vote]))
            check_reject_hypothesis(
                hypotheses.test_stat[winner][vote],
                hypotheses.reject_count, risk_limit)


def run_audit(candidates, max_tests, margins, risk_limit):
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
        ballot_votes = get_ballot(num_winners)
        for vote in ballot_votes:
            update_audit_stats(vote, candidates, hypotheses, margins, risk_limit)
        ballots_tested += 1

        # Step 6
        if hypotheses.reject_count >= num_null_hypotheses:
            return True

    return False


def bravo(votes_array, num_winners, risk_limit, max_tests):
    """BRAVO Ballot-Polling Audit Implementation
    Given an array of votes cast, the number of winners, a risk limit, and a
    maximum number of ballots to test, `bravo` runs an audit on the election
    results to confirm with `risk_limit` confidence that the reported
    `num_winners` winner(s) are indeed the winners.
    """
    candidates = arrange_candidates(votes_array, num_winners)
    margins = get_margins(votes_array, candidates, len(votes_array))

    result = run_audit(candidates, max_tests, margins, risk_limit)
    if result:
        print("Audit completed: the results stand.")
    else:
        print("Too many ballots tested. Perform a full hand-recount of the ballots.")


##### DUMMY DATA ######
VOTES = [0, 0, 0, 0, 0, 100]
NUM_CANDIDATES = len(VOTES)
TOTAL_BALLOTS = sum(VOTES)
NUM_WINNERS = 1
ALPHA = .10
MAX_TESTS = 100
######################


if __name__ == "__main__":
    bravo(VOTES, NUM_WINNERS, ALPHA, MAX_TESTS)
