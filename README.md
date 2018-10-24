# RLA  Project - EECS 498

## RLA Methods to Build
- BRAVO (the Ballot-polling already on Stark's site): https://www.usenix.org/system/files/conference/evtwote12/evtwote12-final27.pdf
- Super-Simple (the comparison part of the existing Stark website): https://www.usenix.org/legacy/events/evtwote10/tech/full_papers/Stark.pdf
- CAST: https://www.stat.berkeley.edu/~stark/Preprints/cast09.pdf
- NEGEXP: https://people.csail.mit.edu/rivest/AslamPopaRivest-OnAuditingElectionsWhenPrecinctsHaveDifferentSizes.pdf
- Bernoulli (We haven't published the method yet but I'll put a draft explanation together for you)

## Goals
- Implement a modern, usable demo of each election method to communicate the intuition behind RLAs and the differences between the various methods
- Proactively consume OpenElection data and compute initial samples for the audit methods above.
- Implement a way to select ballots to be audited in Bernoulli audits (more on this to follow).


## Frontend --> Backend

### BPA (BRAVO)
- n = number of candidates
- V[] = votes for each candidate
- v = total ballots cast
- w = number of winners
- alpha = risk limit
