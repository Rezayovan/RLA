import {API_ROOT, addCandidate, removeCandidate, getCandidateNames, getCandidateVotes, clearValidationErrors, fillTestData, generateErrorAlert, transitionToAuditComplete } from './shared_logic.js';

let numBravoCandidates = 2; // default to 2 candidates
let ballotSequenceNumber = 1; // 1-index the ballot sequence number
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

    formData.append('audit-type', 'bravo');
    formData.append('candidate-votes', JSON.stringify(reportedCandidateVotes));
    formData.append('num-ballots-cast', totalNumBallotsCast);
    formData.append('num-winners', numWinners);
    formData.append('risk-limit', riskLimit);
    formData.append('random-seed', randomSeed);
    formData.append('max-tests', maxTests);

    // Make API call
    axios.post(API_ENDPOINT, formData, {
            headers: {
                'Content-Type': 'multipart/form-data',
            }
        })
        .then((response) => {
            // On success clean up the UI and transition it to in-progress audit state
            transitionInterfaceToInProgress();
            // on response, give back the selected ballot from the back-end
            // TODO: pass in the ballot # to record

            const first_sequence = response.data.sequence_number_to_draw;
            session_id = response.data.session_id;

            continueAudit(first_sequence);
            return console.log(response);
        })
        .catch((error) => {
            return console.error(error);
        });
}

function activateAuditStatusCheckInterval(interval) {
    // Only start this interval once.
    if (auditStatusCheckIntervalBegun) {
        return;
    }

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
                // audit is complete
                const payload = response.data;
                if (payload.audit_complete) {
                    transitionToAuditComplete(payload.completion_message);
                    clearInterval(auditStatusCheckInterval);
                    console.log('Audit completed successfully.');
                }
                return console.log(response);
            })
            .catch((error) => {
                return console.error(error);
            });
    }, interval);
}

// Clean up UI to remove certain buttons and disable input boxes to not mess with audit
function transitionInterfaceToInProgress() {
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
    document.getElementById('ballot-container').appendChild(sectionTitle);

    // Get estimates sample size
    // TODO: get this from the API
    const sampleSize = Math.floor((Math.random() * 100) + 1);
    const sampleSizeElement = document.createElement('div');
    sampleSizeElement.classList.add('alert', 'alert-info', 'd-inline-block');
    sampleSizeElement.id = 'sample-size-alert';
    sampleSizeElement.role = 'alert';
    sampleSizeElement.innerHTML = `Estimated number of ballots to audit: <b>${sampleSize}</b>`;
    document.getElementById('ballot-container').appendChild(sampleSizeElement);

    // Add continue button
    const continueButton = document.createElement('button');
    continueButton.type = 'button';
    continueButton.classList.add('btn', 'btn-success');
    continueButton.id = 'continue-audit';
    continueButton.innerHTML = 'Continue audit';
    document.getElementById('form-container').appendChild(continueButton);

    // Add event listener to continue button
    document.getElementById('continue-audit').addEventListener('click', () => {
        getNextBallotToAudit(); // make request
        // continueAudit(Math.floor((Math.random() * 1000) + 1)); // load next ballot into DOM
    });
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
    const ballotToRecordRow = document.getElementById('ballot-to-record');
    ballotToRecordRow.parentNode.removeChild(ballotToRecordRow);

    const API_ENDPOINT = `${API_ROOT}/send_ballot_votes`
    const formData = new FormData();

    const totalNumBallotsCast = document.getElementById('total-ballots-cast').value;

    formData.append('audit-type', 'bravo');
    formData.append('latest-ballot-votes', JSON.stringify(votes));
    formData.append('num-ballots-cast', totalNumBallotsCast);
    formData.append('session_id', session_id);

    // Make API call
    axios.post(API_ENDPOINT, formData, {
        headers: {
            'Content-Type': 'multipart/form-data',
        }
    })
    .then((response) => {
        // Begin status checker to poll for the completion status every 5 seconds
        activateAuditStatusCheckInterval(5000);

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

    // NOTE: remove these two lines once above API call is implemented
    // continueAudit(Math.floor((Math.random() * 1000) + 1)); // load next ballot into DOM
    // document.getElementById('continue-audit').removeAttribute('disabled');
}

// Tell the user which ballot to cast and record.
function continueAudit(ballotNumToAudit) {
    // once audit is begun, we should change status to 'Continue' and move button below
    // also we gotta disable input boxes above so data cannot be changed
    // also, remove add and remove candidate buttons

    const candidateNames = getCandidateNames();
    const sequenceNum = ballotSequenceNumber++;
    const newBallot = document.createElement('div');
    newBallot.className = 'form-row';
    newBallot.id = 'ballot-to-record';

    const newRow = document.createElement('div');
    newRow.classList.add('col-md-auto', 'mb-3');
    newBallot.appendChild(newRow);

    // eslint-disable-next-line
    let rowContent = `<h6>Draw ballot <b>#${ballotNumToAudit}</b> and record ballot selections</h6>`;

    for (let i = 0; i < candidateNames.length; ++i) {
        rowContent += `\
        <div class="form-check form-check-inline">\
            <input class="form-check-input" type="checkbox" name="ballotSequence${sequenceNum}" id="ballotSeqInlineRadio${sequenceNum}-${i}" value="${candidateNames[i]}">\
            <label class="form-check-label" for="ballotSeqInlineRadio${sequenceNum}-${i}">${candidateNames[i]}</label>\
        </div>`;
    }

    newRow.innerHTML = rowContent;
    document.getElementById('ballot-container').appendChild(newBallot);
}

// =========================
// FOR TESTING PURPOSES ONLY

document.onload = fillTestData();

// FOR TESTING PURPOSES ONLY
// =========================
