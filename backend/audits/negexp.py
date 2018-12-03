import numpy as np

def negexp(vote_shift, risk_limit, precincts):
    precincts_np = np.asarray(precincts)
    candidate_votes = np.sum(precincts_np[:-1], axis=0)
    winner = np.argsort(candidate_votes)[::-1][0]
    loser = np.argsort(candidate_votes)[::][0]
    margin = candidate_votes[winner] - candidate_votes[loser]
    probabilities = []
    for precinct in precincts_np:
        probabilities.append(1 - risk_limit**(2*vote_shift*precinct[-1]/margin))
    return probabilities
