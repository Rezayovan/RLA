import numpy as np
from recordclass import recordclass

from MethodBase import MethodBase

Candidates = recordclass("Candidates", "winners losers")
Hypotheses = recordclass("Hypotheses", "test_stat reject_count")
Bravo_Params = recordclass("BPA_Inputs", "votes_array num_winners risk_limit max_tests")


class Bravo(MethodBase):
    def __init__(self, params):
        self.params = Bravo_Params(*params)


    def run(self):
        self.bravo()

    def bravo(self):
        """BRAVO Ballot-Polling Audit Implementation
        Given an array of votes cast, the number of winners, a risk limit, and a
        maximum number of ballots to test, `bravo` runs an audit on the election
        results to confirm with `risk_limit` confidence that the reported
        `num_winners` winner(s) are indeed the winners.
        """
        params = self.params
        arrange_candidates = self.arrange_candidates
        get_margins = self.get_margins
        run_audit = self.run_audit

        num_candidates = len(params.votes_array)
        assert(params.num_winners > 0 and params.num_winners <= num_candidates)
        assert(params.risk_limit > 0. and params.risk_limit <= 1.)
        if params.max_tests <= 0:
            params.max_tests = sum(params.votes_array)
        else:
            params.max_tests = min(params.max_tests, sum(params.votes_array))

        candidates = arrange_candidates(params.votes_array, params.num_winners)
        margins = get_margins(params.votes_array, candidates, num_candidates)
        result = run_audit(candidates, params.max_tests, margins, params.risk_limit)
        if result:
            print("Audit completed: the results stand.")
        else:
            print("Too many ballots tested. Perform a full hand-recount of the ballots.")

        
    def arrange_candidates(self, votes_array, num_winners):
        """
        From `votes_array`, we can find the winners as the `num_winners` candidates
        (indices) with the most votes. The losers are the rest of the candidates.
        """
        sorted_candidates = sorted(enumerate(votes_array), key=lambda t: t[1], reverse=True)
        winners = set(t[0] for t in sorted_candidates[:num_winners])
        losers = set(t[0] for t in sorted_candidates[num_winners:])

        return Candidates(winners, losers)


    def get_margins(self, votes_array, candidates, num_candidates):
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


    def get_ballot(self, num_winners):
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
            vote = int(input("Enter a vote: "))
            ballot_votes.append(vote)

        return ballot_votes

    def update_hypothesis(self, hypotheses, winner, loser, risk_limit):
        """ Step 5 of the BRAVO algorithm.
        Rejects the null hypothesis corresponding to the test statistic of
        the `winner` and `loser` pair. Increments the null hypothesis
        rejection count.
        """
        if hypotheses.test_stat[winner][loser] >= 1/risk_limit:
            hypotheses.test_stat[winner][loser] = 0
            hypotheses.reject_count += 1

    def update_audit_stats(self, vote, candidates, hypotheses, margins, risk_limit):
        """ Steps 3-5 from the BRAVO algorithm.
        Updates the `test_statistic` and rejects the corresponding null
        hypothesis when appropriate.
        """
        update_hypothesis = self.update_hypothesis

        if vote in candidates.winners: # Step 3
            for loser in candidates.losers:
                hypotheses.test_stat[vote][loser] *= 2*margins[vote][loser]
                update_hypothesis(hypotheses, vote, loser, risk_limit)
        elif vote in candidates.losers: # Step 4
            for winner in candidates.winners:
                hypotheses.test_stat[winner][vote] *= 2*(1-margins[winner][vote])
                update_hypothesis(hypotheses, winner, vote, risk_limit)


    def run_audit(self, candidates, max_tests, margins, risk_limit):
        """
        Runs the algorithm given in "BRAVO" (2012) §7.
        """
        update_audit_stats = self.update_audit_stats
        get_ballot = self.get_ballot

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


            