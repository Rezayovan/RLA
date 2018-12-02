import math

def get_vw_and_vl(votes_array, num_winners):
    sorted_candidates = sorted(enumerate(votes_array), key=lambda t: t[1], reverse=True)

    # Indices of winners in the votes array
    winners = set(t[0] for t in sorted_candidates[:num_winners])
    # Indices of losers in the votes array
    losers = set(t[0] for t in sorted_candidates[num_winners:])

    # find the smallest margin of victory min(winner_votes) - max(loser_votes)
    smallest_winner = min(winners, key=lambda winner_idx: votes_array[winner_idx])
    largest_loser = max(losers, key=lambda winner_idx: votes_array[winner_idx])

    v_w = votes_array[smallest_winner]
    v_l = votes_array[largest_loser]

    return v_w, v_l
