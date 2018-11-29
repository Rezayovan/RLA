# pylint: disable=E0402

import random
import math
import numpy as np
from .shared_objects.BaseAudit import BaseAudit
from .shared_objects.Candidates import Candidates
from .shared_objects.Hypotheses import Hypotheses

class Bravo(BaseAudit):
    """ Ballot-polling audit in Python
    A Python implementation of the BRAVO algorithm described in "BRAVO:
    Ballot-polling Risk-limiting Audits to Verify Outcomes" (Lindeman,
    Stark, and Yates 2012). The full paper can be found on usenix.org
    <https://www.usenix.org/system/files/conference/evtwote12/evtwote12-final27.pdf>
    """
    def __init__(self, votes_array, num_ballots, num_winners,
                 risk_limit, seed, max_tests):
        super().__init__()
        # Set audit variables equal to parameters and sanity check
        assert all(votes >= 0 for votes in votes_array)
        self.votes_array = votes_array
        assert num_ballots >= sum(votes_array)
        self.num_ballots = num_ballots
        self.num_winners = num_winners
        assert 0. < risk_limit <= 1.
        self.risk_limit = risk_limit

        # Need random.Random() instance per Bravo class instance
        # Can then seed this random number object directly
        self.random_gen = random.Random()
        self.seed = seed
        self.random_gen.seed(seed)

        if max_tests <= 0:
            self.max_tests = sum(votes_array)
        else:
            self.max_tests = min(max_tests, sum(votes_array))
        self.num_candidates = len(votes_array)

        self.candidates = self.arrange_candidates()
        self.margins = self.get_margins()
        self.hypotheses = None



    def get_sample_size(self):
        """
        Return the expected sample size of the audit.
        """
        votes_array = self.votes_array
        winners = self.candidates.winners
        losers = self.candidates.losers
        risk_limit = self.risk_limit
        num_ballots = self.num_ballots

        # find the smallest margin of victory min(winner_votes) - max(loser_votes)
        smallest_winner = min(winners, key=lambda winner_idx: votes_array[winner_idx])
        largest_loser = max(losers, key=lambda winner_idx: votes_array[winner_idx])

        v_w = votes_array[smallest_winner]
        v_l = votes_array[largest_loser]

        asn = 0

        if v_w > v_l:
            try:
                s_w = v_w / (v_w + v_l)

                z_w = math.log(2.0 * s_w)
                z_l = math.log(2.0 * (1 - s_w)) if 2.0 * (1 - s_w) > 0 else 0

                n_wl = v_w + v_l

                p_w = v_w / n_wl
                p_l = v_l / n_wl

                p = n_wl / num_ballots

                asn = math.ceil((math.log(1.0 / risk_limit) + (z_w / 2.0)) / (p * ((p_w * z_w) + (p_l * z_l))))
            except ValueError as e:
                asn = 0
                print("Sample size could not be calculated due to an error:", e)

        return asn


    def arrange_candidates(self):
        """
        From `votes_array`, we can find the winners as the `num_winners` candidates
        (indices) with the most votes. The losers are the rest of the candidates.
        """
        sorted_candidates = sorted(enumerate(self.votes_array), \
                key=lambda t: t[1], reverse=True)

        # Indices of winners in the votes array
        winners = set(t[0] for t in sorted_candidates[:self.num_winners])
        # Indices of losers in the votes array
        losers = set(t[0] for t in sorted_candidates[self.num_winners:])

        return Candidates(winners, losers)

    def get_margins(self):
        """
        Return an array `margins` for which for each winner and loser,
        `margins[winner][loser] ≡ votes_array[winner]/(votes_array[winner] + votes_array[loser])`
        is the fraction of votes `winner` was reported to have received among
        ballots reported to show a vote for `winner` or `loser` or both.
        """
        margins = np.zeros([self.num_candidates, self.num_candidates])

        for winner in self.candidates.winners:
            for loser in self.candidates.losers:
                margins[winner][loser] = self.votes_array[winner] \
                        / (self.votes_array[winner] + self.votes_array[loser])

        return margins


    def get_ballot(self):
        """ Step 2 of the BRAVO algorithm.
        Randomly picks a ballot to test and returns a list of its votes.
        The ballot picked is returned to the frontend for the user to input
        actual votes on the ballot. The ballot should be selected using a
        random function seeded by a user-generated seed.
        Note: 'random' should be seeded before this function is called.
        """
        ballot_votes = self.get_votes()
        if len(ballot_votes) > self.num_winners:
            return []
        return ballot_votes

    def update_hypothesis(self, winner, loser):
        """ Step 5 of the BRAVO algorithm.
        Rejects the null hypothesis corresponding to the test statistic of
        the `winner` and `loser` pair. Increments the null hypothesis
        rejection count.
        """
        if self.hypotheses.test_stat[winner][loser] >= 1/self.risk_limit:
            self.hypotheses.test_stat[winner][loser] = 0
            self.hypotheses.reject_count += 1

    def update_audit_stats(self, vote):
        """ Steps 3-5 from the BRAVO algorithm.
        Updates the `test_statistic` and rejects the corresponding null
        hypothesis when appropriate.
        """
        if vote in self.candidates.winners: # Step 3
            for loser in self.candidates.losers:
                self.hypotheses.test_stat[vote][loser] \
                        *= 2*self.margins[vote][loser]
                self.update_hypothesis(vote, loser)
        elif vote in self.candidates.losers: # Step 4
            for winner in self.candidates.winners:
                self.hypotheses.test_stat[winner][vote] \
                        *= 2*(1-self.margins[winner][vote])
                self.update_hypothesis(winner, vote)

    def run_audit(self):
        """
        Runs the algorithm given in "BRAVO" (2012) §7.
        """
        num_winners = len(self.candidates.winners)
        num_losers = len(self.candidates.losers)
        num_candidates = self.num_candidates
        max_tests = self.max_tests

        num_null_hypotheses = num_winners * num_losers
        self.hypotheses = Hypotheses(np.ones([num_candidates, num_candidates]))


        for _ in range(max_tests): # Step 6
            ballot_votes = self.get_ballot()
            assert all(0 <= vote < num_candidates for vote in ballot_votes)
            assert isinstance(ballot_votes, list)
            for vote in ballot_votes:
                self.update_audit_stats(vote)
            # Step 6
            if self.hypotheses.reject_count >= num_null_hypotheses:
                return True

        return False

    def bravo(self):
        """BRAVO Ballot-Polling Audit Implementation
        Given an array of votes cast, the number of winners, a risk limit, and a
        maximum number of ballots to test, `bravo` runs an audit on the election
        results to confirm with `risk_limit` confidence that the reported
        `num_winners` winner(s) are indeed the winners.
        """
        audit_result = self.run_audit()
        self.IS_DONE = True

        print("Audit has been finished")
        if audit_result:
            self.IS_DONE_MESSAGE = "Audit completed: the results stand."
        else:
            self.IS_DONE_MESSAGE = "Too many ballots tested. Perform a full hand-recount of the ballots."

#     def __init__(self, votes_array, num_ballots, num_winners,
#                 risk_limit, seed, max_tests):

if __name__ == "__main__":
    ##### DUMMY DATA ######
    VOTES_ARR = [0, 100]
    TOTAL_VOTES = sum(VOTES_ARR)
    NUM_WINNERS = 1
    ALPHA = .10
    MAX_TESTS = 10
    SEED = 1234567890
    ######################
    bravo = Bravo(VOTES_ARR, TOTAL_VOTES, NUM_WINNERS, ALPHA, SEED, MAX_TESTS)
    bravo.bravo()
