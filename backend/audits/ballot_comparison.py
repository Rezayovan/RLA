from math import log, ceil
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
        self.kaplan_p_value = 1.0
        self.ballots_audited = 1
        self.num_candidates = len(votes_array)

        # TODO seed random

        self.multiplier = self.multiplier()
        self.diluted_margin = self.diluted_margin()

        # TODO how to split candidates into winners and losers
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

    def hand_recount(self):
        # Stop audit and ask user to hand recount everything
        return -1

    def update_p_value(self):
        # Update kaplan p-value (not used unless ballot moves past first state)
        # list of candidate numbers that cvr and human have listed as a vote
        ballot_votes, CVR_votes = self.get_ballot_and_CVR()
        macro = 0
        temp = 0
        for candidate in self.num_candidates:
            in_CVR = candidate in CVR_votes
            in_ballot = candidate in ballot_votes
            if candidate in self.candidates.winners:
                temp = in_CVR - in_ballot
            else:
                temp = in_ballot - in_CVR
            macro += temp/ballots_audited
        # update p-value
        kaplan_p_value *= (1 - 1/total_error_bound)/(1 - (macro/(2 * self.inflation_rate / self.ballots_audited)))

    def run_audit(self):
        sample_size = self.sample_size()
        total_error_bound = 2 * self.inflation_rate / self.diluted_margin
        # Calculate max number of max one vote overstatements allowed before a hand recount
        max_overstatements = ceil(self.diluted_margin * self.tolerance * self.num_ballots)
        # Overstatement is +1, understatement is -1
        overstatements = [0 for candidate in len(self.votes_array)]
        while self.ballots_audited <= sample_size:
            update_p_value()
            # list of candidate numbers that cvr and human have listed as a vote
            ballot_votes, CVR_votes = self.get_ballot_and_CVR()
            # Ballot is an overvote and CVR shows valid vote. Mark everything in CVR as an overstatement.
            if len(ballot_votes) > num_winners and len(CVR_votes) <= num_winners:
                for candidate in CVR_votes:
                    overstatements[candidate] += 1
            # CVR is an overvote but Ballot is valid, list all candidates on ballot as an understatement
            elif len(ballot_votes) <= num_winners and len(CVR_votes) > num_winners:
                for candidate in ballot_votes:
                    overstatements[candidate] -= 1
            # CVR and Human both show overvote, dont do anything
            elif len(ballot_votes) > num_winners and len(CVR_votes) > num_winners:
                continue
            # Guaranteed neither CVR or Human are overvoted ballots
            else:
                num_mismatches = 0
                for candidate in num_candidates:
                    in_CVR = candidate in CVR_votes
                    in_ballot = candidate in ballot_votes

                    if not in_ballot and in_CVR:
                        num_mismatches += 1
                        # check if number of errors is greater than 1 on a single ballot
                        if num_mismatches > 1:
                            hand_recount()
                        # an overstatement is found
                        overstatements[candidate] += 1
                        # if candidate is a winner
                        # TODO fix line 124 to actually check
                        if candidate in self.candidates.winners:
                            if overstatements[candidate] > max_overstatements:
                                hand_recount()
                    if in_ballot and not in_CVR:
                        num_mismatches += 1
                        # check if number of errors is greater than 1 on a single ballot
                        if num_mismatches > 1:
                            hand_recount()
                        # an understatement is found
                        overstatements[candidate] -= 1
            self.ballots_audited += 1

        # If at this point, no overstatement is above max_overstatements
        # continue hand recount using Kaplan P-Value, stop if p-value
        while(self.ballots_audited < self.num_ballots):
            update_p_value()
            if self.kaplan_p_value <= self.risk_limit:
                break
            self.ballots_audited += 1
        # Audit is finished

            

                    
                    














