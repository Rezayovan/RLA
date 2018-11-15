Super Simple Ballot Auditing Notes

Terms
Diluted Margin - the smallest margin of victory in votes among the contests divided by the total number of votes cast across all contests
Apparent Winner - winning candidate based on apparent outcome
Apparent Loser - losing candidate based on apparent outcome
Risk Limiting Audit - guaranteed minimum chance of progressing to a full hand recount if apparent outcome is incorrect
Risk - maximum chance audit fails to correct an incorrect apparent outcome
Risk Measuring Audit - reports strength of the evidence that the outcome is correct
Measured Risk - P-Value of hypothesis that the outcome is incorrect given data collected by the audit
Overstatement - an error that increases on apparent margin (ex. Machine saw underbite, user saw vote for apparent loser)
Understatement - an error that decreases apparent margin (ex. Machine saw overbite, user saw vote for apparent winner)
MACRO (maximum across-race relative overstatement) - 

Notes
- Sample a set number of ballots depending on risk limit 
    - If number of ballots that overstated the ballot by 1 vote are more than half of diluted margin, keep sampling past 1st round
    - If a ballot sampled overstated margin by two votes, keep sampling past 1st round
- Apparent outcome is wrong if for some apparent winner and some apparent loser, the apparent margin is less than the overstatement errors minus the understatement errors
    - Another way to think of this: The difference between understatement errors and overstatement errors is more than the apparent margin
- This audit method doesn’t work with Instant Runoff Voting or other preference voting schemes

Version 1 of Super Simple Audit
1. Pick simultaneous risk limit, α, which is the largest chance that an incorrect outcome will not be corrected by the audit
2. Pick an error inflation rate, γ >= 100%, γ controls a tradeoff between initial sample size and the amount of additional counting required when the sample finds too many overstatements. 
    #. The larger γ is, the larger the initial sample size is, but the less additional counting will be required if too many overstatements are found. 
    #. Default is γ = 110%
3. Pick a tolerance,  λ < 100%, for one-vote maximum overstatements as a percentage of the diluted margin, μ. 
    #. If the percentage of ballots in the sample with one-vote maximum overstatements is no more than λμ and there are no two-vote overstatements, the audit can stop.
    #. The larger λ is, the larger initial sample size will have to be to give high confidence that even though the error rate in the sample is a large fraction of the diluted margin, the error rate for the contest as a whole (which we have only audited a subset of) is less than the diluted margin
4. Calculate the sample size multiplier, ρ. All values α, γ, λ can all be decided before the start of the audit process $$ρ = (-log(α))/( (1/(2γ)) + λlog( 1 - (1/(2γ)) ) )$$
5. Find the diluted margin, μ - user should give results and we should calculate.
6. Draw at least ρ/μ at random and audit them - output which random ballots that should be audited.
    1. If the percentage of ballots in the sample with one-vote maximum overstatements is not more than λμ and no ballot has a two-vote overstatement, the audit can stop.
        1. All contests are then confirmed at a simultaneous risk no greater than α

Cases where Audit can stop at first stage
Recalculate Pkm, when Pam inequality is satisfied, you can stop
Batch-style, when recomputing Pam, all rounds should be used in calculation
1. Sample finds no more than k ballots that overstate any margin by 1 vote and no ballot that overstates any margin by 2 votes
    1. We want to find the smallest sample size n, such that P(n, k, 0; U, γ) <= α 
	1. U is defined as the error bound across all ballots: U = 2γN/V = 2γ/μ
    2. Audit can stop if n >= -2γ(logα + klog(1 - (1/(2y))))/μ
2. Sample percentage of ballots that overstate the margin by 1 vote is no more than a fraction λ of the diluted margin μ and no sampled ballot overstates the margin by 2 votes
    1. 











