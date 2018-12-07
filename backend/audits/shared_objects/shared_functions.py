"""
Splits the inputted votes_array (list of candidates and their
respective votes) into a Candidate object with winners and losers.
"""
from .Candidates import Candidates

def arrange_candidates(votes_array, num_winners):
    """
    From `votes_array`, we can find the winners as the `num_winners` candidates
    (indices) with the most votes. The losers are the rest of the candidates.
    """
    sorted_candidates = sorted(enumerate(votes_array), \
            key=lambda t: t[1], reverse=True)

    # Indices of winners in the votes array
    winners = set(t[0] for t in sorted_candidates[:num_winners])
    # Indices of losers in the votes array
    losers = set(t[0] for t in sorted_candidates[num_winners:])

    return Candidates(winners, losers)

def get_winners(votes_array, num_winners):
    """ Reports the winners.
    For use when the losers are not relevant to the caller.
    """
    return arrange_candidates(votes_array, num_winners).winners
