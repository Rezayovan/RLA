import {
    API_ROOT,
    addCandidateAndTally,
    removeCandidate,
    getCandidateVotes,
    clearValidationErrors,
    generateErrorAlert,
    // fillTestData,
    getCandidateSampleTallies,
    transitionToAuditComplete,
    removeElement
} from './shared_logic.js';

const AUDIT_TYPE = 'bayesian_polling';

let numCandidates = 2; // default to 2 candidates

let auditBegun = false;

document.getElementById('add-candidate').addEventListener('click', () => {
    numCandidates++;
    addCandidateAndTally(numCandidates);
});

document.getElementById('remove-candidate').addEventListener('click', () => {
    const candidates = document.querySelectorAll('#candidates-container .form-row');
    if (!candidates.length) return;

    numCandidates--;
    removeCandidate();
});

document.getElementById('begin-bayesian').addEventListener('click', () => {
    beginBayesianAudit();
});

function clearBayesianErrors() {
    // Remove error div if it exists
    clearValidationErrors();
    const auditAlert = document.getElementById('audit-complete-alert');
    if (auditAlert) {
        removeElement('audit-complete-alert');
    }
}

function beginBayesianAudit() {
    clearBayesianErrors();

    // Obtain data from form
    const reportedCandidateVotes = getCandidateVotes();
    const sampleTallies = getCandidateSampleTallies();

    const totalNumBallotsCast = parseInt(document.getElementById('total-ballots-cast').value, 10);
    const numWinners = parseInt(document.getElementById('num-winners').value, 10);
    const riskLimit = parseFloat(document.getElementById('risk-limit').value);
    const randomSeed = document.getElementById('random-seed').value;
    const numTrials = parseInt(document.getElementById('num-trials').value, 10);

    // Too few candidates
    if (reportedCandidateVotes.length < 2) {
        const errorMsg = `Not enough candidates to begin audit. Please enter at least 2 candidates to proceed.`;
        return generateErrorAlert('audit-info', errorMsg);
    }

    if (numWinners <= 0 || numWinners > reportedCandidateVotes.length) {
        const errorMsg = 'Invalid number of winners. Number of winners must be greater than 0 and less than the total number of candidates.';
        return generateErrorAlert('audit-info', errorMsg);
    }

    const reportedCandidateVotesSum = reportedCandidateVotes.reduce((a, b) => a + b, 0);
    if (reportedCandidateVotesSum > totalNumBallotsCast * numWinners) {
        const errorMsg = `Reported candidate votes (${reportedCandidateVotesSum}) are greater than the total number of votes multiplied by the number of winners (${totalNumBallotsCast * numWinners}). Please correct this and try again.`;
        return generateErrorAlert('audit-info', errorMsg);
    }

    const reportedTalliesSum = sampleTallies.reduce((a, b) => a + b, 0);
    if (reportedTalliesSum > totalNumBallotsCast) {
        const errorMsg = `Reported sample tallies votes (${reportedTalliesSum}) are greater than the total number of votes (${totalNumBallotsCast}). Something is probably wrong, and this audit won't help. Try another audit, or hand count all ballots.`;
        return generateErrorAlert('audit-info', errorMsg);
    }

    if (randomSeed.length < 20) {
        const errorMsg = 'Random seed does not meet minimum length requirements. Please input a random seed of length 20 or greater.';
        return generateErrorAlert('audit-info', errorMsg);
    }

    if (riskLimit <= 0 || riskLimit > 100) {
        const errorMsg = 'Risk limit must be between 1% and 100%.';
        return generateErrorAlert('audit-info', errorMsg);
    }

    if (numTrials < 1) {
        const errorMsg = 'Number of trials should be greater than 1.';
        return generateErrorAlert('audit-info', errorMsg);
    }

    // Setup API call
    const API_ENDPOINT = `${API_ROOT}/perform_audit`
    const formData = new FormData();

    formData.append('audit_type', AUDIT_TYPE);
    formData.append('candidate_votes', JSON.stringify(reportedCandidateVotes));
    formData.append('sample_tallies', JSON.stringify(sampleTallies));
    formData.append('num_ballots_cast', totalNumBallotsCast);
    formData.append('num_winners', numWinners);
    formData.append('risk_limit', riskLimit);
    formData.append('random_seed', randomSeed);
    formData.append('num_trials', numTrials);

    // Make API call
    axios.post(API_ENDPOINT, formData, {
            headers: {
                'Content-Type': 'multipart/form-data',
            }
        })
        .then((response) => {
            const payload = response.data;

            const message = payload.completion_message;
            const flag = payload.flag;

            finishAudit(message, flag);
            return console.log(response);
        })
        .catch((error) => {
            return console.error(error);
        });

}

function finishAudit(message, flag) {
    if (!auditBegun) {
        const auditTitleElt = document.createElement('h3');
        auditTitleElt.classList.add('mt-3');
        auditTitleElt.innerHTML = 'Audit';
        document.getElementById('audit-container').appendChild(auditTitleElt);
        auditBegun = true;
    }

    if (auditBegun) {
        removeElement('audit-complete-alert');
    }
    transitionToAuditComplete(message, flag);
}

// =========================
// FOR TESTING PURPOSES ONLY

// document.onload = fillTestData();

// FOR TESTING PURPOSES ONLY
// =========================
