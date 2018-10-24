import numpy as np

# Inputs from frontend
# n = number of candidates
# V[] = votes for each candidate
V = [10,30,40,2,5,100]
n = size(V)
# v = total ballots cast
v = sum(V)
# w = number of winners
w = 2
# a = risk limit
a = .10

# Similarly define l as number of losers
l = n-w

T = np.ones( [w, l] )
s = np.zero( [w, l] )

# Determine winners and losers
W = []
#sort(V, reverse=True)
W = []
L = []

# Winners are indices of the 'w' candidates with most votes
W = set(t[0] for t in sorted(enumerate(V), reverse=True)[:w])
# Losers are all the rest
L = set(t[0] for t in sorted(enumerate(V), reverse=True)[w:])

# Set s values
for winner in range(w):
    for loser in range(l):
        s[winner][loser] = (V[winner] / (V[winner] + V[loser]))

# Audit ballots
while():
    #Step 2
    b = randint(0, v) # Pick random ballot
    # Send 'b' to frontend - TODO API call
    # Recieve list of 'votes' (at most size w) where each element is in [0,n) - TODO API call
    votes = [] # size in [0, w)
    for (vote in votes):
        vote = randint(0, n) # TODO: remove this
        if (vote in W): #Step 3
            for (loser in L):
                T[vote][loser] *= s[vote][loser]/.5
        if (vote in L): #Step 4
            for (winner in W):
                T[winner][vote] *= (1-s[winner][vote])/.5
    
