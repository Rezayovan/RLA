from .shared_objects.BaseAudit import BaseAudit
# TODO: figure out how to import bptool correctly

class BayesianPolling(BaseAudit):
    """ Bayesian ballot-polling audit in Python
    A wrapper class around Ron Rivest's [2018-bptool](https://github.com/ron-rivest/2018-bptool).
    """
    def __init__(self, num_candidates, sample_tallies, num_ballots, num_winners, risk_limit, seed, reported_winners):
        super().__init__()
        self.num_candidates = num_candidates
        self.sample_tallies = sample_tallies
        self.num_ballots = num_ballots
        self.num_winners = num_winners
        self.risk_limit = risk_limit
        self.seed = seed
        self.reported_winners = reported_winners

    def run_audit(self):
        bayesian_winners = bptool.compute_win_probs(self.sample_talies, self.num_ballots, self.num_winners, self.seed)
        for winner in bayesian_winners:
            if not(winner.i in self.reported_winners and winner.p >= 1 - self.risk_limit):
                return False
        return True

    def bayesian_bpa(self):
        audit_result = self.run_audit()
        self.IS_DONE = True

        print("Audit has been finished")
        if audit_result:
            self.IS_DONE_MESSAGE = "Audit completed: the results stand."
            self.IS_DONE_FLAG = "success"
        else:
            self.IS_DONE_MESSAGE = "Too many ballots tested. Use a larger sample size. This may indicate that your reported winners are incorrect."
            self.IS_DONE_FLAG = "danger"
