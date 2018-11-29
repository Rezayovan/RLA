import {API_ROOT, addCandidate, removeCandidate, getCandidateNames, getCandidateVotes, clearValidationErrors, fillTestData, generateErrorAlert } from './shared_logic.js';

let numBravoCandidates = 2; // default to 2 candidates
let auditStatusCheckIntervalBegun = false;
let session_id = "";

document.getElementById('add-candidate').addEventListener('click', () => {
    addCandidate(++numBravoCandidates);
});

document.getElementById('remove-candidate').addEventListener('click', () => {
    const candidates = document.querySelectorAll('#candidates-container .form-row');
    if (!candidates.length) return;

    numBravoCandidates--;
    removeCandidate();
});

document.getElementById('begin-bravo').addEventListener('click', () => {
    beginBravoAudit();
});

function beginBravoAudit() {
    // Remove error div if it exists
    clearValidationErrors();

    // Obtain data from form
    const reportedCandidateVotes = getCandidateVotes();

    const totalNumBallotsCast = document.getElementById('total-ballots-cast').value;
    const numWinners = document.getElementById('num-winners').value;
    const riskLimit = document.getElementById('risk-limit').value;
    const randomSeed = document.getElementById('random-seed').value;
    const maxTests = document.getElementById('max-tests').value;

    // Too few candidates
    if (reportedCandidateVotes.length < 2) {
        const errorMsg = `Not enough candidates to begin audit. Please enter at least 2 candidates to proceed.`;
        return generateErrorAlert('audit-info', errorMsg);
    }

    // Too many winners
    // TODO: is num_winners == number of candidates OK?
    if (numWinners > reportedCandidateVotes.length) {
        const errorMsg = `Too many winners inputted. Please lower the number of winners to proceed.`;
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

    // At this point, data has been (partially) validated

    // Setup API call
    const API_ENDPOINT = `${API_ROOT}/perform_audit`
    const formData = new FormData();

    formData.append('audit_type', 'bravo');
    formData.append('candidate_votes', JSON.stringify(reportedCandidateVotes));
    formData.append('num_ballots_cast', totalNumBallotsCast);
    formData.append('num_winners', numWinners);
    formData.append('risk_limit', riskLimit);
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

function activateAuditStatusCheckInterval(interval) {
    // Only start this interval once.
    if (auditStatusCheckIntervalBegun) return;

    auditStatusCheckIntervalBegun = true;

    // Check for audit completion status every {interval} seconds
    const auditStatusCheckInterval = setInterval(() => {
        const API_ENDPOINT = `${API_ROOT}/check_audit_status`
        const formData = new FormData();

        formData.append('session_id', session_id);

        // Make API call
        axios.post(API_ENDPOINT, formData, {
                headers: {
                    'Content-Type': 'multipart/form-data',
                }
            })
            .then((response) => {
                const payload = response.data;
                if (payload.audit_complete) {
                    transitionToAuditComplete(payload.completion_message, payload.flag);
                    clearInterval(auditStatusCheckInterval);
                    console.log('Audit completed successfully.');
                }
                // return console.log(response);
            })
            .catch((error) => {
                return console.error(error);
            });
    }, interval);
}

// Clean up UI to remove certain buttons and disable input boxes to not mess with audit
function transitionInterfaceToInProgress(sampleSize, firstSequence) {
    // Disable text inputs
    const auditInputs = document.querySelectorAll('#audit-info input');
    for (const input of auditInputs) {
        input.setAttribute('disabled', '');
    }

    // Disable add/remove candidate buttons
    const addCandidateButton = document.getElementById('add-candidate');
    addCandidateButton.setAttribute('disabled', '');
    const removeCandidateButton = document.getElementById('remove-candidate');
    removeCandidateButton.setAttribute('disabled', '');

    // Remove begin button
    const beginButton = document.getElementById('begin-bravo');
    beginButton.setAttribute('disabled', '');

    // Show section title
    const sectionTitle = document.createElement('h3');
    sectionTitle.classList.add('mt-3');
    sectionTitle.innerHTML = 'Audit';
    document.getElementById('audit-container').appendChild(sectionTitle);

    const ballotContainerDiv = document.createElement('div');
    ballotContainerDiv.id = 'ballot-container';
    document.getElementById('audit-container').appendChild(ballotContainerDiv);

    // Display estimated sample size
    const sampleSizeElement = document.createElement('div');
    sampleSizeElement.classList.add('alert', 'alert-info', 'd-inline-block');
    sampleSizeElement.id = 'sample-size-alert';
    sampleSizeElement.role = 'alert';
    sampleSizeElement.innerHTML = `Estimated number of ballots to audit: <b>${sampleSize}</b>`;
    ballotContainerDiv.appendChild(sampleSizeElement);

    // Display checkboxes
    const candidateNames = getCandidateNames();
    const newBallot = document.createElement('div');
    newBallot.className = 'form-row';
    newBallot.id = 'ballot-to-record';

    const newRow = document.createElement('div');
    newRow.classList.add('col-md-auto', 'mb-3');
    newBallot.appendChild(newRow);

    // eslint-disable-next-line
    let rowContent = `<h6>Draw ballot <b id='ballot-sequence-num'>#${firstSequence}</b> and record ballot selections</h6>`;

    for (let i = 0; i < candidateNames.length; ++i) {
        rowContent += `\
        <div class="form-check form-check-inline">\
            <input class="form-check-input" type="checkbox" name="ballotSeqInlineRadio-${i}" id="ballotSeqInlineRadio-${i}" value="${candidateNames[i]}">\
            <label class="form-check-label" for="ballotSeqInlineRadio-${i}">${candidateNames[i]}</label>\
        </div>`;
    }

    newRow.innerHTML = rowContent;
    document.getElementById('ballot-container').appendChild(newBallot);

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

export function transitionToAuditComplete(message, flag) {
    const auditCompleteDiv = document.createElement('div');
    auditCompleteDiv.classList.add('alert', `alert-${flag}`, 'mt-3');
    auditCompleteDiv.role = 'alert';
    auditCompleteDiv.innerHTML = message;

    const element = document.getElementById('ballot-container');
    if (element) {
        element.parentNode.removeChild(element);
    }

    document.getElementById('audit-container').appendChild(auditCompleteDiv);
}

function getNextBallotToAudit() {
    // Cannot continue until next ballot to audit is returned from the back-end API
    document.getElementById('continue-audit').setAttribute('disabled', '');

    const voteNodes = document.querySelectorAll('#ballot-container .form-row');
    if (voteNodes.length == 0) {
        return console.error('voteNodes is empty in the Audit section. I am sad.');
    }
    const latestVoteCheckBoxes = voteNodes[voteNodes.length - 1].getElementsByTagName('input');

    const votes = [];
    for (let i = 0; i < latestVoteCheckBoxes.length; ++i) {
        if (latestVoteCheckBoxes[i].checked) {
            votes.push(i);
        }
    }

    console.log('Vote data:', votes);

    // Remove checkbox container to load new one
    // const ballotToRecordRow = document.getElementById('ballot-to-record');
    // ballotToRecordRow.parentNode.removeChild(ballotToRecordRow);

    const API_ENDPOINT = `${API_ROOT}/send_ballot_votes`
    const formData = new FormData();

    const totalNumBallotsCast = document.getElementById('total-ballots-cast').value;

    formData.append('audit_type', 'bravo');
    formData.append('latest_ballot_votes', JSON.stringify(votes));
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
        activateAuditStatusCheckInterval(3000);

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
    const voteNodes = document.querySelectorAll('#ballot-container .form-row');
    if (voteNodes.length == 0) {
        return console.error('voteNodes is empty in the Audit section. I am sad.');
    }
    const latestVoteCheckBoxes = voteNodes[voteNodes.length - 1].getElementsByTagName('input');

    for (let i = 0; i < latestVoteCheckBoxes.length; ++i) {
        if (latestVoteCheckBoxes[i].checked) {
            latestVoteCheckBoxes[i].checked = false;
        }
    }

    document.getElementById('ballot-sequence-num').innerHTML = ballotNumToAudit;
}

// =========================
// FOR TESTING PURPOSES ONLY

document.onload = fillTestData();

// FOR TESTING PURPOSES ONLY
// =========================
