from .shared_objects.arrange_candidates import get_winners
from .bptool.bptool import compute_win_probs

class BayesianPolling():
    """ Bayesian ballot-polling audit in Python
    A wrapper class around Ron Rivest's [2018-bptool](https://github.com/ron-rivest/2018-bptool).
    """
    def __init__(self, votes_array, num_ballots, num_winners,\
            risk_limit, seed, sample_tallies, num_trials):
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
        self.num_trials = num_trials

    def bayesian_polling_audit(self):
        """
        Uses compute_win_probs to verify the election results.
        Returns true IFF the reported winners and Bayesian projected
        winners match AND the probability of each projected winner
        winning is greater than the significance level.
        """
        reported_winners = get_winners(self.votes_array, self.num_winners)

        bayesian_win_probs = compute_win_probs([self.sample_tallies],\
                                             [self.num_ballots],\
                                             self.seed,\
                                             self.num_trials,\
                                             self.votes_array,\
                                             self.num_winners)
        bayesian_win_probs.sort(key=lambda t: t[1], reverse=True)
        bayesian_winners = bayesian_win_probs[:self.num_winners]
        reported_set = {(w+1) for w in reported_winners}

        if not len(bayesian_winners) == len(reported_winners):
            return False
        for projected in bayesian_winners:
            if not projected[0] in reported_set:
                return False
            if not projected[1] >= 1 - self.risk_limit:
                return False
        return True

    def run_audit(self):
        audit_result = self.bayesian_polling_audit()

        if audit_result:
            return "Audit completed: the results stand.", "success"

        return "Failed to confirm the results. Sample a larger portion of the ballots. This may indicate that your reported winners are incorrect.", "danger"
