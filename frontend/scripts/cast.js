import {
    API_ROOT,
    addCandidate,
    removeCandidate,
    getCandidateNames,
    clearValidationErrors,
    fillTestData,
    generateErrorAlert,
    activateAuditStatusCheckInterval,
    disableInputsAndButtons,
    setupAuditDOM,
    removeElement
} from './shared_logic.js';

const AUDIT_TYPE = 'cast';

let numCandidates = 2; // default to 2 candidates
let auditStatusCheckIntervalBegun = false;
let session_id = '';

let numBatchesInputted = 1;

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
    const batchSize = parseInt(document.getElementById('batch-size').value, 10);
    const numBatches = parseInt(document.getElementById('num-batches').value, 10);

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

    // TODO: is this too limiting?
    if (threshold * numBatches >= 100) {
        const errorMsg = 'Threshold of escalation multiplied by the number of batches must be less than 100.';
        return generateErrorAlert('audit-info', errorMsg);
    }

    disableInputsAndButtons();

    loadBatchInputDOM(reportedCandidateNames, numBatches);
}

function loadBatchInputDOM(reportedCandidateNames, numBatches) {
    const CVRTitleElt = document.createElement('h3');
    CVRTitleElt.classList.add('mt-3');
    CVRTitleElt.innerHTML = 'Input Vote Data';
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
    manageBatchInputs();

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

// Get current values from inputs
// Save values in data structure to send to API later on (2D array)
// Clear inputs
function manageBatchInputs() {
    const inputNodes = document.querySelectorAll('#cvr-inputs .candidate-input');

    const batchVotes = [];
    for (const node of inputNodes) {
        batchVotes.push(parseInt(node.value, 10));
        node.value = '';
    }

    // TODO: validation on batchVotes array

    cvrDataInputs.push(batchVotes);
}

function beginCast() {
    // do stuff
}

// =========================
// FOR TESTING PURPOSES ONLY

document.onload = fillTestData();

// FOR TESTING PURPOSES ONLY
// =========================
