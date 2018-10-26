import numpy as np

'''
Inputs from frontend
 - n = number of candidates
 - V[] = votes for each candidate
 - v = total ballots cast
 - w = number of winners
 - alpha = risk limit
 - M = max number of ballots to audit
'''

##### DUMMY DATA ######
V = [10,30,40,2,5,100]
n = size(V)
v = sum(V)
w = 2
alpha = .10
M = n/2
######################


def bravo():

    # l := number of losers
    l = n-w

    T = np.ones([n, n])
    s = np.zeros([n, n])

    # Winners are indices of the 'w' candidates with most votes
    sorted_candidates = sorted(enumerate(V), key=lambda t: t[1], reverse=True)
    W = set(t[0] for t in sorted_candidates[:w])
    # Losers are all the rest
    L = set(t[0] for t in sorted_candidates[w:])

    # Set s values
    for winner in W:
        for loser in L:
            s[winner][loser] = (V[winner] / (V[winner] + V[loser]))

    # Audit ballots
    ballots_tested = 0 # number of ballots tested
    reject_count = 0
    num_null_hypotheses = w*l
    while ballots_tested < M: # Step 6
        # Step 2: TODO - use seed
        # b = randrange(0, v) # Pick random ballot
        # Send 'b' to frontend - TODO API call
        # Receive list of 'votes' (at most size w) where each element is in [0,n) - TODO API call
        votes = [] # size in [0, w)
        # TODO: replace below loop with API calls
        for _ in range(w):
            votes.append(5)
        for vote in votes:
            if vote in W: # Step 3
                for loser in L:
                    T[vote][loser] *= s[vote][loser]/.5
                    if T[vote][loser] >= 1/alpha: # Step 5
                        # Mark this T's corresp. null hyp. as rejected
                        T[vote][loser] = 0
                        reject_count += 1
            elif vote in L: # Step 4
                for winner in W:
                    T[winner][vote] *= (1-s[winner][vote])/.5
                    if T[winner][vote] >= 1/alpha: # Step 5
                        # Mark this T's corresp. null hyp. as rejected
                        T[winner][vote] = 0
                        reject_count += 1
        ballots_tested += 1

        # Step 6
        if reject_count >= num_null_hypotheses:
            print("Audit completed: the results stand.")
            return

    print("Too many ballots were drawn. Perform a full hand-recount.")

if __name__ == "__main__":
    bravo()
