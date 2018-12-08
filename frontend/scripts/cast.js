import {
    API_ROOT,
    STATUS_CHECK_INTERVAL,
    addCandidate,
    removeCandidate,
    getCandidateNames,
    clearValidationErrors,
    fillTestData,
    generateErrorAlert,
    activateAuditStatusCheckInterval,
    disableInputsAndButtons,
    removeElement
} from './shared_logic.js';

const AUDIT_TYPE = 'cast';

let numCandidates = 2; // default to 2 candidates
let auditStatusCheckIntervalBegun = false;
let session_id = '';

let numBatchesInputted = 1;
let batchSize;

let cvrDataInputs = [];

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
    addCandidate(numCandidates, true);
});

document.getElementById('remove-candidate').addEventListener('click', () => {
    const candidates = document.querySelectorAll('#candidates-container .form-row');
    if (!candidates.length) return;

    numCandidates--;
    removeCandidate();
});

document.getElementById('continue-to-cvr').addEventListener('click', () => {
    clearValidationErrors();
    handleContinueToCVR();
});

function handleContinueToCVR() {
    const reportedCandidateNames = getCandidateNames();

    const numWinners = parseInt(document.getElementById('num-winners').value, 10);
    const riskLimit = parseFloat(document.getElementById('risk-limit').value);
    const threshold = parseFloat(document.getElementById('threshold').value);
    const randomSeed = document.getElementById('random-seed').value;
    const numStages = parseInt(document.getElementById('num-stages').value, 10);
    const numBatches = parseInt(document.getElementById('num-batches').value, 10);

    batchSize = parseInt(document.getElementById('batch-size').value, 10);

    // Validations

    if (reportedCandidateNames.length < 2) {
        const errorMsg = `Not enough candidates to begin audit. Please enter at least 2 candidates to proceed.`;
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

    if (threshold <= 0 || threshold > 100) {
        const errorMsg = 'Threshold must be between 1% and 100%.';
        return generateErrorAlert('audit-info', errorMsg);
    }

    if (numWinners <= 0 || numWinners > reportedCandidateNames.length) {
        const errorMsg = 'Invalid number of winners. Number of winners must be greater than 0 and less than the total number of candidates.';
        return generateErrorAlert('audit-info', errorMsg);
    }

    if (numStages < 1) {
        const errorMsg = 'Please enter a non-negative number of stages.';
        return generateErrorAlert('audit-info', errorMsg);
    }

    if (numBatches < 1) {
        const errorMsg = 'Please enter a non-negative number of batches.';
        return generateErrorAlert('audit-info', errorMsg);
    }

    if (batchSize < 1) {
        const errorMsg = 'Please enter a non-negative batch size.';
        return generateErrorAlert('audit-info', errorMsg);
    }

    if (numStages > batchSize) {
        const errorMsg = 'Please ensure that the number of stages is less than the batch size.';
        return generateErrorAlert('audit-info', errorMsg);
    }

    if (threshold * numBatches >= 100) {
        const errorMsg = 'Threshold of escalation multiplied by the number of batches must be less than 100.';
        return generateErrorAlert('audit-info', errorMsg);
    }

    disableInputsAndButtons('audit-info');

    loadBatchInputDOM(reportedCandidateNames, numBatches);
}

function loadBatchInputDOM(reportedCandidateNames, numBatches) {
    const CVRTitleElt = document.createElement('h3');
    CVRTitleElt.classList.add('mt-3');
    CVRTitleElt.innerHTML = 'Input Reported Vote Data';
    document.getElementById('cvr-container').appendChild(CVRTitleElt);

    const CVRToInputElt = document.createElement('h6');
    CVRToInputElt.innerHTML = 'Please input the votes per candidate for batch <b>#<span id="cvr-number-to-input">1</span></b>.';
    document.getElementById('cvr-container').appendChild(CVRToInputElt);

    const formRowDiv = document.createElement('div');
    formRowDiv.classList.add('form-row');
    formRowDiv.id = 'cvr-inputs';

    let candidateNum = 0;
    for (const candidateName of reportedCandidateNames) {
        formRowDiv.innerHTML += `\
            <div class="col-md-2 col-lg-2 mb-3">\
                <label for="candidate-${candidateNum}">${candidateName}</label>\
                <input type="number" class="form-control candidate-input" id="candidate-${candidateNum}" min="0" placeholder="0" value="0">\
            </div>`;
        ++candidateNum;
    }

    document.getElementById('cvr-container').appendChild(formRowDiv);

    // No need for continue button. Just put a "Begin audit" button.
    if (numBatches == 1) {
        addAndSetupBeginAuditBtn();
    } else {
        const nextCVRBtn = document.createElement('button');
        nextCVRBtn.classList.add('btn', 'btn-primary');
        nextCVRBtn.type = 'button';
        nextCVRBtn.id = 'input-next-cvr';
        nextCVRBtn.innerHTML = 'Input next result';
        document.getElementById('cvr-container').appendChild(nextCVRBtn);

        document.getElementById('input-next-cvr').addEventListener('click', () => {
            setupNextBatch(numBatches);
        });
    }
}

function setupNextBatch(numBatches) {
    try {
        manageInitialBatchInputs();
    } catch (e) {
        return console.log("Batch invalid.");
    }

    document.getElementById('cvr-number-to-input').innerHTML = ++numBatchesInputted;

    // Need to ask user for batch inputs until numBatches == numBatchesInputted
    if (numBatchesInputted == numBatches) {
        // This is the final one to input, change the btn to begin audit
        removeElement('input-next-cvr');
        addAndSetupBeginAuditBtn();
    }
}

function addAndSetupBeginAuditBtn() {
    const beginAuditBtn = document.createElement('button');
    beginAuditBtn.classList.add('btn', 'btn-success');
    beginAuditBtn.type = 'button';
    beginAuditBtn.id = 'begin-cast';
    beginAuditBtn.innerHTML = 'Begin audit';
    document.getElementById('cvr-container').appendChild(beginAuditBtn);

    document.getElementById('begin-cast').addEventListener('click', () => {
        beginCast();
    });
}

function getBatchInputs(inputNodes, idForErrors) {
    const batchVotes = [];
    for (const node of inputNodes) {
        if (!node.value) {
            batchVotes.push(0);
        } else {
            const voteVal = parseInt(node.value, 10);

            if (voteVal < 0) {
                const errorMsg = 'Please enter non-negative votes.';
                throw generateErrorAlert(idForErrors, errorMsg);
            }

            batchVotes.push(voteVal);
        }
    }

    const batchVotesSum = batchVotes.reduce((a, b) => a + b, 0);
    if (batchVotesSum > batchSize) {
        const errorMsg = `The entered votes for batch #${numBatchesInputted} exceed the batch size. Please correct this to proceed.`;
        throw generateErrorAlert(idForErrors, errorMsg);
    }

    return batchVotes;
}

// Get current values from inputs
// Save values in data structure to send to API later on (2D array)
// Clear inputs
function manageInitialBatchInputs() {
    clearValidationErrors();

    const inputNodes = document.querySelectorAll('#cvr-inputs .candidate-input');
    const batchVotes = getBatchInputs(inputNodes, 'cvr-container');

    // Clear the values for the next batch
    for (const node of inputNodes) {
        node.value = '';
    }

    cvrDataInputs.push(batchVotes);
}

function beginCast() {
    // Get final batch of votes before beginning audit
    manageInitialBatchInputs();

    const numWinners = parseInt(document.getElementById('num-winners').value, 10);
    const riskLimit = parseFloat(document.getElementById('risk-limit').value);
    const threshold = parseFloat(document.getElementById('threshold').value);
    const randomSeed = document.getElementById('random-seed').value;
    const numStages = parseInt(document.getElementById('num-stages').value, 10);
    const batchSize = parseInt(document.getElementById('batch-size').value, 10);
    const numBatches = parseInt(document.getElementById('num-batches').value, 10);

    console.log(cvrDataInputs);

    // Setup API call
    const API_ENDPOINT = `${API_ROOT}/perform_audit`
    const formData = new FormData();

    formData.append('audit_type', AUDIT_TYPE);
    formData.append('initial_cvr_data', JSON.stringify(cvrDataInputs));
    formData.append('num_candidates', numCandidates);
    formData.append('num_winners', numWinners);
    formData.append('risk_limit', riskLimit);
    formData.append('random_seed', randomSeed);
    formData.append('threshold', threshold);
    formData.append('batch_size', batchSize);
    formData.append('num_batches', numBatches);
    formData.append('num_stages', numStages);

    // Make API call
    axios.post(API_ENDPOINT, formData, {
            headers: {
                'Content-Type': 'multipart/form-data',
            }
        })
        .then((response) => {
            // Disable CVR container
            disableInputsAndButtons('cvr-container');

            // Set session
            session_id = response.data.session_id;

            // Begin status checker to poll for the completion status every STATUS_CHECK_INTERVAL seconds
            if (!auditStatusCheckIntervalBegun) {
                auditStatusCheckIntervalBegun = true;
                activateAuditStatusCheckInterval(STATUS_CHECK_INTERVAL, session_id);
            }

            const sequenceNumberToDraw = response.data.sequence_number_to_draw;

            populateAuditContainer(sequenceNumberToDraw);

            // handle response
            return console.log(response);
        })
        .catch((error) => {
            return console.error(error);
        });
}

function populateAuditContainer(initialBatchToAudit) {
    const reportedCandidateNames = getCandidateNames();

    const auditTitleElt = document.createElement('h3');
    auditTitleElt.classList.add('mt-3');
    auditTitleElt.innerHTML = 'Audit';
    document.getElementById('audit-container').appendChild(auditTitleElt);

    const containerDiv = document.createElement('div');
    containerDiv.id = 'ballot-container';
    document.getElementById('audit-container').appendChild(containerDiv);

    const CVRToInputElt = document.createElement('h6');
    CVRToInputElt.innerHTML = `Please input the votes per candidate for batch <b>#<span id="batch-to-audit">${initialBatchToAudit}</span></b>.`;
    containerDiv.appendChild(CVRToInputElt);

    // Add candidate inputs
    const formRowDiv = document.createElement('div');
    formRowDiv.classList.add('form-row');
    formRowDiv.id = 'audit-inputs';

    let candidateNum = 0;
    for (const candidateName of reportedCandidateNames) {
        formRowDiv.innerHTML += `\
            <div class="col-md-2 col-lg-2 mb-3">\
                <label for="candidate-${candidateNum}">${candidateName}</label>\
                <input type="number" class="form-control candidate-input" id="candidate-${candidateNum}" min="0" placeholder="0" value="0">\
            </div>`;
        ++candidateNum;
    }

    containerDiv.appendChild(formRowDiv);

    // Add continue button
    const continueBtn = document.createElement('button');
    continueBtn.classList.add('btn', 'btn-success');
    continueBtn.type = 'button';
    continueBtn.id = 'continue-audit';
    continueBtn.innerHTML = 'Continue audit';
    containerDiv.appendChild(continueBtn);

    document.getElementById('continue-audit').addEventListener('click', () => {
        getNextBallotToAudit();
    });
}

function getNextBallotToAudit() {
    clearValidationErrors();

    const inputNodes = document.querySelectorAll('#audit-inputs .candidate-input');
    let batchVotes;

    try {
        batchVotes = getBatchInputs(inputNodes, 'audit-container');
    } catch (e) {
        return console.log("Batch invalid.");
    }

    // Clear the values for the next batch
    for (const node of inputNodes) {
        node.value = '';
    }

    // Cannot continue until next ballot to audit is returned from the back-end API
    document.getElementById('continue-audit').setAttribute('disabled', '');

    // Setup API call
    const API_ENDPOINT = `${API_ROOT}/send_ballot_votes`
    const formData = new FormData();

    formData.append('audit_type', AUDIT_TYPE);
    formData.append('session_id', session_id);
    formData.append('batch_votes', JSON.stringify(batchVotes));

    console.log(batchVotes);

    // Make API call
    axios.post(API_ENDPOINT, formData, {
            headers: {
                'Content-Type': 'multipart/form-data',
            }
        })
        .then((response) => {
            if (response.status === 204) {
                // Let timer interval handle UI change.
                return console.log("Audit complete.");
            }

            const sequenceNumberToDraw = response.data.sequence_number_to_draw;

            document.getElementById('batch-to-audit').innerHTML = sequenceNumberToDraw;

            // Re-enable the button
            document.getElementById('continue-audit').removeAttribute('disabled');

            return console.log(response);
        })
        .catch((error) => {
            return console.error(error);
        });
}

// =========================
// FOR TESTING PURPOSES ONLY

document.onload = fillTestData();

// FOR TESTING PURPOSES ONLY
// =========================