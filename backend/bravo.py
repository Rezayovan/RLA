import numpy as np
from random import randrange

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
n = len(V)
v = sum(V)
w = 2
alpha = .10
M = n/2
######################

def bravo():

    # l := number of losers
    l = n-w

    T = np.ones( [w, l] )
    s = np.zeros( [w, l] )
    print(T)
    print(s)

    # Winners are indices of the 'w' candidates with most votes
    sortedCandidates = sorted(enumerate(V), key=lambda t:t[1], reverse=True)
    W = set(t[0] for t in sortedCandidates[:w])
    # Losers are all the rest
    L = set(t[0] for t in sortedCandidates[w:])
    print(W, L)

    # Set s values
    for winner in range(w):
        for loser in range(l):
            s[winner][loser] = ( V[winner] / (V[winner] + V[loser]) )

    # Audit ballots
    m = 0 # number of ballots tested
    reject_count = 0
    num_null_hypotheses = w*l
    while m < M: # Step 6
        # Step 2: TODO - use seed
        # b = randrange(0, v) # Pick random ballot ## DUMMY DATA
        # Send 'b' to frontend - TODO API call
        # Recieve list of 'votes' (at most size w) where each element is in [0,n) - TODO API call
        votes = [] # size in [0, w)
        for _ in range(w): # TODO: remove this once API calls in place
            # votes.append(randrange(0, n))
            votes.append(1)
        for vote in votes:
            if vote in W: # Step 3
                for loser in L:
                    print(vote, loser)
                    # T[vote][loser] *= s[vote][loser]/.5
                    val = s[vote][loser]/.5
                    T[vote][loser] *= val
                    if T[vote][loser] >= 1/alpha: # Step 5
                        T[vote][loser] = 0 # Mark T's corresp. null hyp. as rejected
                        reject_count += 1
            elif vote in L: # Step 4
                for winner in W:
                    val = (1-s[winner][vote])/.5
                    T[winner][vote] *= val
                    if T[winner][vote] >= 1/alpha: # Step 5
                        T[winner][vote] = 0 # Mark T's corresp. null hyp. as rejected
                        reject_count += 1
        # Step 6
        if reject_count >= num_null_hypotheses:
            print("Audit completed: the results stand.")
            return

    print("Too many ballots were drawn. Perform a full hand-recount.")

if __name__ == "__main__":
    bravo()