from math import log
import random
from Bravo_OOP import Candidates

class BallotComparison:
    def __init__(self, votes_array, num_ballots, num_winners, risk_limit, seed, inflation_rate, tolerance):
        self.votes_array = votes_array
        self.num_ballots = num_ballots
        self.num_winners = num_winners
        self.risk_limit = risk_limit
        self.seed = seed
        self.inflation_rate = inflation_rate
        self.tolerance = tolerance

        # TODO seed random

        self.multiplier = self.multiplier()
        self.diluted_margin = self.diluted_margin()

        self.candidates = self.arrange_candidates()

    def arrange_candidates(self):
        """
        From `votes_array`, we can find the winners as the `num_winners` candidates
        (indices) with the most votes. The losers are the rest of the candidates.
        """
        votes_array = self.votes_array
        num_winners = self.num_winners

        sorted_candidates = sorted(enumerate(votes_array), key=lambda t: t[1], reverse=True)

        # Indices of winners in the votes array
        winners = set(t[0] for t in sorted_candidates[:num_winners])
        # Indices of losers in the votes array
        losers = set(t[0] for t in sorted_candidates[num_winners:])

        return Candidates(winners, losers)


    def multiplier(self):
         return -log(self.risk_limit)/(1/(2*self.inflation_rate) + self.tolerance * log(1 - 1/(2*self.inflation_rate)))

    def diluted_margin(self):
        sorted_votes = sorted(self.votes_array, reverse=True)
        smallest_margin = sorted_votes[self.num_winners - 1] - sorted_votes[self.num_winners]
        return smallest_margin/self.num_ballots

    def sample_size(self):
        return self.multiplier/self.diluted_margin

    def get_votes(self, ballot_number):
        """
        Returns ballot votes and corresponding CVR votes for given ballot number.
        """
        # TODO: Reza or Jad
        return ballot_votes, CVR_votes

    def get_sequence_number(self):
        """Returns random sequence number to draw ballot from."""
        num_ballots = self.num_ballots
        ballot_to_draw = self.random_gen.randint(1, num_ballots)
        return ballot_to_draw

    def get_ballot_and_CVR(self):
        """ Step 2 of the BRAVO algorithm.
        Randomly picks a ballot to test and returns a set of its votes and
        those of the corresponding CVR.
        (A vote is denoted by a candidate's index's presence in the set.)
        The ballot picked is returned to the frontend for the user to input
        actual votes on the ballot and the vote recorded on the corresponding
        CVR.  The ballot should be selected using a
        random function seeded by a user-generated seed.
        Note: 'random' should be seeded before this function is called.
        """
        num_winners = self.num_winners
        ballot_votes, CVR_votes = self.get_votes(get_sequence_number)
        # TODO: handle under- and overvotes
 
        return ballot_votes, CVR_votes


    def run_audit(self):
        num_candidates = len(votes_array)
        sample_size = self.sample_size()
        # Overstatement is +1, understatement is -1
        overstatements = [0 for candidate in len(self.votes_array)]
        for _ in sample_size:
            ballot_votes, CVR_votes = self.get_ballot_and_CVR()
            # Ballot is an overvote and CVR shows valid vote. Mark everything in CVR as an overstatement.
            if len(ballot_votes) > num_winners and len(CVR_votes) <= num_winners:
                for candidate in CVR_votes:
                    overstatements[candidate] += 1
            elif len(ballot_votes) <= num_winners and len(CVR_votes) > num_winners:
                for candidate in ballot_votes:
                    overstatements[candidate] -= 1
            elif len(ballot_votes) > num_winners and len(CVR_votes) > num_winners:
                continue
            else:
                num_mismatches = 0
                for candidate in num_candidates:
                    in_CVR = candidate in CVR_votes
                    in_ballot = candidate in ballot_votes
                    if in_ballot and in_CVR:
                        del ballot_votes[candidate]
                        del CVR_votes[candidate]
