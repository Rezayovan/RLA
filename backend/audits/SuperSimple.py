from math import log, ceil
import random
from .shared_objects.arrange_candidates import arrange_candidates
from .shared_objects.Candidates import Candidates
from .shared_objects.BaseAudit import BaseAudit

class SuperSimple(BaseAudit):
    def __init__(self, votes_array, num_ballots, num_winners, risk_limit, seed, inflation_rate, tolerance):
        super().__init__()
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

        self.random_gen = random.Random()
        self.random_gen.seed(int(seed))

        self.multiplier = self.multiplier()
        self.diluted_margin = self.diluted_margin()
        self.total_error_bound = 2 * self.inflation_rate / self.diluted_margin
        self.candidates = arrange_candidates(votes_array, num_winners)

    def multiplier(self):
        return -log(self.risk_limit)/(1/(2*self.inflation_rate) + self.tolerance * log(1 - 1/(2*self.inflation_rate)))

    def diluted_margin(self):
        sorted_votes = sorted(self.votes_array, reverse=True)
        smallest_margin = sorted_votes[self.num_winners - 1] - sorted_votes[self.num_winners]
        return smallest_margin/self.num_ballots

    def sample_size(self):
        return self.multiplier/self.diluted_margin

    def get_votes_wrapper(self):
        """
        Returns ballot votes and corresponding CVR votes for given ballot number.
        """
        votes = self.get_votes()
        return votes[0], votes[1]

    def get_ballot_and_CVR(self):
        """
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
        ballot_votes, CVR_votes = self.get_votes_wrapper()

        return ballot_votes, CVR_votes

    def hand_recount(self):
        # Stop audit and ask user to hand recount everything
        self.IS_DONE_MESSAGE = "The audit cannot verify the election results. Please perform a full hand recount."
        self.IS_DONE_FLAG = "danger"
        self.IS_DONE = True
        return -1

    def audit_success(self):
        self.IS_DONE_MESSAGE = "Audit completed: results stand."
        self.IS_DONE_FLAG = "success"
        self.IS_DONE = True
        return 0

    def update_p_value(self, ballot_votes, CVR_votes):
        # Update kaplan p-value (not used unless ballot moves past first state)
        # list of candidate numbers that cvr and human have listed as a vote
        macro = 0
        maxwinner = 0
        maxloser = 0
        temp = 0
        for candidate in range(self.num_candidates):
            in_CVR = candidate in CVR_votes
            in_ballot = candidate in ballot_votes
            if candidate in self.candidates.winners:
                temp = in_CVR - in_ballot
                maxwinner = max(temp, maxwinner)
            else:
                temp = in_ballot - in_CVR
                maxloser = max(temp, maxloser)
        macro = (maxwinner + maxloser)/self.ballots_audited
        # update p-value
        self.kaplan_p_value *= (1 - 1/self.total_error_bound)/(1 - (macro/(2 * self.inflation_rate / self.ballots_audited)))

    def run_audit(self):
        sample_size = self.sample_size()
        if sample_size >= self.num_ballots:
            return self.hand_recount()
        # Calculate max number of max one vote overstatements allowed before a hand recount
        max_overstatements = ceil(self.diluted_margin * self.tolerance * self.num_ballots)
        # Overstatement is +1, understatement is -1
        overstatements = [0 for candidate in range(len(self.votes_array))]
        while self.ballots_audited <= sample_size:
            # list of candidate numbers that cvr and human have listed as a vote
            ballot_votes, CVR_votes = self.get_ballot_and_CVR()
            self.update_p_value(ballot_votes, CVR_votes)
            # Ballot is an overvote and CVR shows valid vote. Mark everything in CVR as an overstatement.
            if len(ballot_votes) > self.num_winners and len(CVR_votes) <= self.num_winners:
                for candidate in CVR_votes:
                    overstatements[candidate] += 1
            # CVR is an overvote but Ballot is valid, list all candidates on ballot as an understatement
            elif len(ballot_votes) <= self.num_winners and len(CVR_votes) > self.num_winners:
                for candidate in ballot_votes:
                    overstatements[candidate] -= 1
            # CVR and Human both show overvote, dont do anything
            elif len(ballot_votes) > self.num_winners and len(CVR_votes) > self.num_winners:
                continue
            # Guaranteed neither CVR or Human are overvoted ballots
            else:
                num_mismatches = 0
                for candidate in range(self.num_candidates):
                    in_CVR = candidate in CVR_votes
                    in_ballot = candidate in ballot_votes
                    if not in_ballot and in_CVR:
                        num_mismatches += 1
                        # check if number of errors is greater than 1 on a single ballot
                        if num_mismatches > 1:
                            return self.hand_recount()
                        # an overstatement is found
                        overstatements[candidate] += 1
                    if in_ballot and not in_CVR:
                        num_mismatches += 1
                        # check if number of errors is greater than 1 on a single ballot
                        if num_mismatches > 1:
                            return self.hand_recount()
                        # an understatement is found
                        overstatements[candidate] -= 1
            self.ballots_audited += 1
        # Check if Audit needs to be continued
        can_stop = True
        for candidate in range(self.num_candidates):
            # if candidate is a winner
            if candidate in self.candidates.winners:
                if overstatements[candidate] > max_overstatements:
                    can_stop = False

        if can_stop:
            return self.audit_success()

        # If at this point, no overstatement is above max_overstatements
        # continue hand recount using Kaplan P-Value, stop if p-value
        while(self.ballots_audited < self.num_ballots):
            ballot_votes, CVR_votes = self.get_ballot_and_CVR()
            self.update_p_value(ballot_votes, CVR_votes)
            if self.kaplan_p_value <= self.risk_limit:
                break
            self.ballots_audited += 1
        # Audit is finished
        if self.ballots_audited < self.num_ballots:
            return self.audit_success()
        else:
            return self.hand_recount()

if __name__ == "__main__":
    #     def __init__(self, votes_array, num_ballots, num_winners, risk_limit, seed, inflation_rate, tolerance):
    params = [[10, 5], 15, 1, .05, 345678765432, 1.1, .5]
    ss = SuperSimple(*params)
    ss.run_audit()
