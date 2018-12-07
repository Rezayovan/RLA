import {
    API_ROOT,
    addCandidate,
    removeCandidate,
    getCandidateNames,
    getCandidateVotes,
    clearValidationErrors,
    fillTestData,
    generateErrorAlert,
    activateAuditStatusCheckInterval,
    disableInputsAndButtons,
    setupAuditDOM
} from './shared_logic.js';

const AUDIT_TYPE = 'super_simple';

let numCandidates = 2; // default to 2 candidates
let auditStatusCheckIntervalBegun = false;
let session_id = '';

// Revoke session_id and end audit on backend
window.addEventListener('unload', () => {
    if (session_id === '') return;

    const API_ENDPOINT = `${API_ROOT}/end_audit`
    const formData = new FormData();
    formData.append('session_id', session_id);
    navigator.sendBeacon(API_ENDPOINT, formData);
});

document.getElementById('add-candidate').addEventListener('click', () => {
    numCandidates++;
    addCandidate(numCandidates);
});

document.getElementById('remove-candidate').addEventListener('click', () => {
    const candidates = document.querySelectorAll('#candidates-container .form-row');
    if (!candidates.length) return;

    numCandidates--;
    removeCandidate();
});

document.getElementById('begin-super-simple').addEventListener('click', () => {
    beginSuperSimpleAudit();
});

function beginSuperSimpleAudit() {
    // Remove error div if it exists
    clearValidationErrors();

    // Obtain data from form
    const reportedCandidateVotes = getCandidateVotes();

    const totalNumBallotsCast = parseInt(document.getElementById('total-ballots-cast').value, 10);
    const numWinners = parseInt(document.getElementById('num-winners').value, 10);
    const riskLimit = parseFloat(document.getElementById('risk-limit').value);
    const inflationRate = parseFloat(document.getElementById('inflation-rate').value);
    const tolerance = parseFloat(document.getElementById('tolerance').value);
    const randomSeed = document.getElementById('random-seed').value;
    const maxTests = parseInt(document.getElementById('max-tests').value, 10);

    // Too few candidates
    if (reportedCandidateVotes.length < 2) {
        const errorMsg = `Not enough candidates to begin audit. Please enter at least 2 candidates to proceed.`;
        return generateErrorAlert('audit-info', errorMsg);
    }

    // Too many winners
    // TODO: is num_winners == number of candidates OK?
    if (numWinners <= 0 || numWinners > reportedCandidateVotes.length) {
        const errorMsg = 'Invalid number of winners. Number of winners must be greater than 0 and less than the total number of candidates.';
        return generateErrorAlert('audit-info', errorMsg);
    }

    const reportedCandidateVotesSum = reportedCandidateVotes.reduce((a, b) => a + b, 0);
    if (reportedCandidateVotesSum > totalNumBallotsCast) {
        const errorMsg = `Reported candidate votes (${reportedCandidateVotesSum}) are greater than the total number of votes (${totalNumBallotsCast}). Please correct this and try again.`;
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

    if (inflationRate < 100 || inflationRate >= 200) {
        const errorMsg = 'Inflation rate must be between 100% and 199%.';
        return generateErrorAlert('audit-info', errorMsg);
    }

    if (tolerance <= 0 || tolerance >= 100) {
        const errorMsg = 'Tolerance must be between 1% and 100%.';
        return generateErrorAlert('audit-info', errorMsg);
    }

    if (maxTests < 1) {
        const errorMsg = 'Please enter a non-negative maximum number of tests.';
        return generateErrorAlert('audit-info', errorMsg);
    }

    // At this point, data has been (partially) validated

    // Setup API call
    const API_ENDPOINT = `${API_ROOT}/perform_audit`
    const formData = new FormData();

    formData.append('audit_type', AUDIT_TYPE);
    formData.append('candidate_votes', JSON.stringify(reportedCandidateVotes));
    formData.append('num_ballots_cast', totalNumBallotsCast);
    formData.append('num_winners', numWinners);
    formData.append('risk_limit', riskLimit);
    formData.append('inflation_rate', inflationRate);
    formData.append('tolerance', tolerance);
    formData.append('random_seed', randomSeed);
    formData.append('max_tests', maxTests);

    // Make API call
    axios.post(API_ENDPOINT, formData, {
            headers: {
                'Content-Type': 'multipart/form-data',
            }
        })
        .then((response) => {
            const estSampleSize = response.data.estimated_sample_size

            const firstSequence = response.data.sequence_number_to_draw;
            session_id = response.data.session_id;
            console.log("Session ID:", session_id);

            // On success clean up the UI and transition it to in-progress audit state
            transitionInterfaceToInProgress(estSampleSize, firstSequence);

            // continueAudit(first_sequence);
            return console.log(response);
        })
        .catch((error) => {
            return console.error(error);
        });
}

// Clean up UI to remove certain buttons and disable input boxes to not mess with audit
function transitionInterfaceToInProgress(sampleSize, firstSequence) {
    disableInputsAndButtons('audit-info');
    setupAuditDOM(sampleSize);

    // Display ballot checkboxes
    const candidateNames = getCandidateNames();
    const newBallot = document.createElement('div');
    newBallot.className = 'form-row';
    newBallot.id = 'ballot-to-record';

    const newRow = document.createElement('div');
    newRow.classList.add('col-md-auto', 'mb-3');
    newBallot.appendChild(newRow);

    let rowContent = `<h6>Draw ballot <b>#<span id='ballot-sequence-num'>${firstSequence}</span></b> and record selections</h6>`;

    for (let i = 0; i < candidateNames.length; ++i) {
        rowContent += `\
        <div class="form-check form-check-inline">\
            <input class="form-check-input" type="checkbox" name="ballotSeqInlineRadio-${i}" id="ballotSeqInlineRadio-${i}" value="${candidateNames[i]}">\
            <label class="form-check-label" for="ballotSeqInlineRadio-${i}">${candidateNames[i]}</label>\
        </div>`;
    }

    newRow.innerHTML = rowContent;
    document.getElementById('ballot-container').appendChild(newBallot);

    // Display CVR checkboxes
    const newCVR = document.createElement('div');
    newCVR.className = 'form-row';
    newCVR.id = 'cvr-to-record';

    const newCVRRow = document.createElement('div');
    newCVRRow.classList.add('col-md-auto', 'mb-3');
    newCVR.appendChild(newCVRRow);

    let CVRRowContent = `<h6>Draw CVR for ballot <b id='CVR-sequence-num'>#${firstSequence}</b> and record selections</h6>`;

    for (let i = 0; i < candidateNames.length; ++i) {
        CVRRowContent += `\
        <div class="form-check form-check-inline">\
            <input class="form-check-input" type="checkbox" name="CVRSeqInlineRadio-${i}" id="CVRSeqInlineRadio-${i}" value="${candidateNames[i]}">\
            <label class="form-check-label" for="CVRSeqInlineRadio-${i}">${candidateNames[i]}</label>\
        </div>`;
    }

    newCVRRow.innerHTML = CVRRowContent;
    document.getElementById('ballot-container').appendChild(newCVR);

    // Add continue button
    const continueButton = document.createElement('button');
    continueButton.type = 'button';
    continueButton.classList.add('btn', 'btn-success');
    continueButton.id = 'continue-audit';
    continueButton.innerHTML = 'Continue audit';
    document.getElementById('ballot-container').appendChild(continueButton);

    // Add event listener to continue button
    document.getElementById('continue-audit').addEventListener('click', () => {
        getNextBallotToAudit();
    });
}

function getNextBallotToAudit() {
    // Cannot continue until next ballot to audit is returned from the back-end API
    document.getElementById('continue-audit').setAttribute('disabled', '');

    const voteNodes = document.querySelectorAll('#ballot-container .form-row');

    const ballotVoteNodes = voteNodes[0];
    if (ballotVoteNodes.length == 0) {
        return console.error('ballotVoteNodes is empty in the Audit section. I am sad.');
    }
    const latestBallotVoteCheckBoxes = ballotVoteNodes.getElementsByTagName('input');

    const ballotVotes = [];
    for (let i = 0; i < latestBallotVoteCheckBoxes.length; ++i) {
        if (latestBallotVoteCheckBoxes[i].checked) {
            ballotVotes.push(i);
        }
    }
    console.log('Ballot vote data:', ballotVotes);

    const cvrVoteNodes = voteNodes[1];
    if (cvrVoteNodes.length == 0) {
        return console.error('cvrVoteNodes is empty in the Audit section. I am sad.');
    }
    const latestCVRVoteNodesCheckBoxes = cvrVoteNodes.getElementsByTagName('input');

    const CVRVotes = [];
    for (let i = 0; i < latestCVRVoteNodesCheckBoxes.length; ++i) {
        if (latestCVRVoteNodesCheckBoxes[i].checked) {
            CVRVotes.push(i);
        }
    }
    console.log('CVR vote data:', CVRVotes);

    const API_ENDPOINT = `${API_ROOT}/send_ballot_votes`
    const formData = new FormData();

    const totalNumBallotsCast = parseInt(document.getElementById('total-ballots-cast').value, 10);

    const total_votes = {
        'paper_record': ballotVotes,
        'cvr': CVRVotes
    };

    console.log(total_votes);

    formData.append('audit_type', AUDIT_TYPE);
    formData.append('paper_record_and_cvr', JSON.stringify(total_votes));
    formData.append('num_ballots_cast', totalNumBallotsCast);
    formData.append('session_id', session_id);

    // Make API call
    axios.post(API_ENDPOINT, formData, {
        headers: {
            'Content-Type': 'multipart/form-data',
        }
    })
    .then((response) => {
        // Begin status checker to poll for the completion status every 3 seconds
        if (!auditStatusCheckIntervalBegun) {
            auditStatusCheckIntervalBegun = true;
            activateAuditStatusCheckInterval(3000, session_id);
        }

        if (response.status === 204) {
            // Let timer interval handle UI change.
            console.log("Audit complete.");
            return;
        }

        const next_sequence = response.data.sequence_number_to_draw;
        continueAudit(next_sequence); // load next ballot into DOM

        // Re-enable the button
        document.getElementById('continue-audit').removeAttribute('disabled');

        // TODO: use response to extract the next ballot to audit and pass it into continueAudit function below
        return console.log(response);
    })
    .catch((error) => {
        return console.error(error);
    });
}

// Tell the user which ballot to cast and record.
function continueAudit(ballotNumToAudit) {
    const ballotVoteNode = document.getElementById('ballot-to-record');
    const latestBallotVoteCheckBoxes = ballotVoteNode.getElementsByTagName('input');

    // Reset check boxes
    for (let i = 0; i < latestBallotVoteCheckBoxes.length; ++i) {
        if (latestBallotVoteCheckBoxes[i].checked) {
            latestBallotVoteCheckBoxes[i].checked = false;
        }
    }

    const cvrVoteNode = document.getElementById('cvr-to-record');
    const latestCvrVoteCheckBoxes = cvrVoteNode.getElementsByTagName('input');

    // Reset check boxes
    for (let i = 0; i < latestCvrVoteCheckBoxes.length; ++i) {
        if (latestCvrVoteCheckBoxes[i].checked) {
            latestCvrVoteCheckBoxes[i].checked = false;
        }
    }

    document.getElementById('ballot-sequence-num').innerHTML = ballotNumToAudit;
}

// =========================
// FOR TESTING PURPOSES ONLY

document.onload = fillTestData();

// FOR TESTING PURPOSES ONLY
// =========================
