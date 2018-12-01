import math

def get_bravo_vw_and_vl(votes_array, num_winners):
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

# def get_bravo_sample_size(votes_array, risk_limit, num_ballots):
#     """
#     Return the expected sample size of the audit.
#     """
#     sorted_candidates = sorted(enumerate(votes_array), key=lambda t: t[1], reverse=True)

#     # Indices of winners in the votes array
#     winners = set(t[0] for t in sorted_candidates[:self.num_winners])
#     # Indices of losers in the votes array
#     losers = set(t[0] for t in sorted_candidates[self.num_winners:])

#     # find the smallest margin of victory min(winner_votes) - max(loser_votes)
#     smallest_winner = min(winners, key=lambda winner_idx: votes_array[winner_idx])
#     largest_loser = max(losers, key=lambda winner_idx: votes_array[winner_idx])

#     v_w = votes_array[smallest_winner]
#     v_l = votes_array[largest_loser]

#     asn = 0

#     if v_w > v_l:
#         try:
#             s_w = v_w / (v_w + v_l)

#             z_w = math.log(2.0 * s_w)
#             z_l = math.log(2.0 * (1 - s_w)) if 2.0 * (1 - s_w) > 0 else 0

#             n_wl = v_w + v_l

#             p_w = v_w / n_wl
#             p_l = v_l / n_wl

#             p = n_wl / num_ballots

#             asn = math.ceil((math.log(1.0 / risk_limit) + (z_w / 2.0)) / (p * ((p_w * z_w) + (p_l * z_l))))
#         except ValueError as e:
#             asn = 0
#             print("Sample size could not be calculated due to an error:", e)

#     return asn
