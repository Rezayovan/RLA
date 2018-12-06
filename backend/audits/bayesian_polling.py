# pylint: disable=E0402

from .shared_objects.BaseAudit import BaseAudit
from .bptools.bptools import compute_win_probs

class BayesianPolling(BaseAudit):
    """ Bayesian ballot-polling audit in Python
    A wrapper class around Ron Rivest's [2018-bptool](https://github.com/ron-rivest/2018-bptool).
    """
    def __init__(self, votes_array, num_ballots, num_winners,\
            risk_limit, seed, sample_tallies):
        super().__init__()
        assert all(votes >= 0 for votes in votes_array)
        self.votes_array = votes_array
        assert num_ballots >= sum(votes_array)
        self.num_ballots = num_ballots
        assert num_winners < len(votes_array)
        self.num_winners = num_winners
        self.sample_tallies = sample_tallies
        assert 0. < risk_limit <= 1.
        self.risk_limit = risk_limit
        self.seed = seed

    def bayesian_audit(self):
        reported_winners = self.arrange_candidates().winners
        bayesian_winners = compute_win_probs(self.sample_tallies, self.num_ballots, self.num_winners, self.seed)
        for winner in bayesian_winners:
            if not((winner.i in reported_winners)\
                    and (winner.p >= 1 - self.risk_limit)):
                return False
        return True

    def run_audit(self):
        audit_result = self.run_audit()
        self.IS_DONE = True

        print("Audit has been finished")
        if audit_result:
            self.IS_DONE_MESSAGE = "Audit completed: the results stand."
            self.IS_DONE_FLAG = "success"
        else:
            self.IS_DONE_MESSAGE = "Failed to confirm the results. Sample a larger portion of the ballots. This may indicate that your reported winners are incorrect."
            self.IS_DONE_FLAG = "danger"
