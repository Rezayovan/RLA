export const  API_ROOT = 'http://127.0.0.1:5000';
export const STATUS_CHECK_INTERVAL = 1500;

export function removeElement(elementID) {
    const element = document.getElementById(elementID);
    if (element) {
        element.parentNode.removeChild(element);
    }
}

export function addCandidate(numCandidates, onlyNames) {
    const newCandidate = document.createElement('div');
    newCandidate.className = 'form-row';
    newCandidate.innerHTML = `\
    <div class="col-md-4 mb-3">\
        <label for="candidate${numCandidates}">Candidate ${numCandidates} name</label>\
        <input type="text" class="form-control" id="candidate${numCandidates}" placeholder="Name" value='Candidate ${numCandidates}'>\
    </div>`;
    if (!onlyNames) {
        newCandidate.innerHTML += `\
        <div class="col-md-4 mb-3">\
            <label for="candidate${numCandidates}-votes">Candidate ${numCandidates} votes</label>\
            <input type="number" class="form-control" id="candidate${numCandidates}-votes" placeholder="0" min="0">\
        </div>`;
    }
    document.getElementById('candidates-container').appendChild(newCandidate);
}

export function addCandidateAndTally(numCandidates) {
    const newCandidate = document.createElement('div');
    newCandidate.className = 'form-row';
    newCandidate.innerHTML = `\
    <div class="col-md-4 mb-3">\
        <label for="candidate${numCandidates}">Candidate ${numCandidates} name</label>\
        <input type="text" class="form-control candidate-name" id="candidate${numCandidates}" placeholder="Name">\
    </div>
    <div class="col-md-4 mb-3">\
        <label for="candidate${numCandidates}-votes">Candidate ${numCandidates} votes</label>\
        <input type="number" class="form-control candidate-vote" id="candidate${numCandidates}-votes" placeholder="0" min="0">\
    </div>\
    <div class="col-md-4 mb-3">\
        <label for="candidate${numCandidates}-sample-tally">Candidate ${numCandidates} sample tally</label>\
        <input type="number" class="form-control sample-tally" id="candidate${numCandidates}-sample-tally" placeholder="0" min="0">\
    </div>`;
    document.getElementById('candidates-container').appendChild(newCandidate);
}

export function removeCandidate() {
    const candidates = document.querySelectorAll('#candidates-container .form-row');
    const lastCandidate = candidates[candidates.length - 1];
    if (lastCandidate) {
        document.getElementById('candidates-container').removeChild(lastCandidate);
    }
}

export function getCandidateNames() {
    const candidateNameNodes = document.querySelectorAll('#candidates-container .candidate-name');
    const candidateNames = [];
    for (const node of candidateNameNodes) {
        candidateNames.push(node.value);
    }
    return candidateNames;
}

export function getCandidateVotes() {
    const candidateVoteNodes = document.querySelectorAll('#candidates-container .candidate-vote');
    const candidateVotes = [];
    for (const node of candidateVoteNodes) {
        candidateVotes.push(parseInt(node.value, 10));
    }
    return candidateVotes;
}

export function getCandidateSampleTallies() {
    const candidateSampleTallyNodes = document.querySelectorAll('#candidates-container .sample-tally');
    const candidateSampleTallies = [];
    for (const node of candidateSampleTallyNodes) {
        candidateSampleTallies.push(parseInt(node.value, 10));
    }
    return candidateSampleTallies;
}

export function clearValidationErrors() {
    const validationErrors = document.querySelectorAll('.validation-error');
    if (validationErrors.length > 0) {
        for (const errorNode of validationErrors) {
            errorNode.parentNode.removeChild(errorNode);
        }
    }
}

export function generateErrorAlert(idToAppendTo, errorMessage) {
    const errorDiv = document.createElement('div');
    errorDiv.classList.add('alert', 'alert-danger', 'validation-error', 'mt-3');
    errorDiv.role = 'alert';
    errorDiv.innerHTML = errorMessage;

    document.getElementById(idToAppendTo).appendChild(errorDiv);
}

export function disableInputsAndButtons(containerToDisable) {
    // Disable text inputs
    const auditInputs = document.querySelectorAll(`#${containerToDisable} input`);
    for (const input of auditInputs) {
        input.setAttribute('disabled', '');
    }

    // Disable buttons
    const auditBtns = document.querySelectorAll(`#${containerToDisable} button`);
    for (const button of auditBtns) {
        button.setAttribute('disabled', '');
    }
}

export function setupAuditDOM(sampleSize) {
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
    sampleSizeElement.classList.add('alert', 'alert-primary', 'd-inline-block');
    sampleSizeElement.id = 'sample-size-alert';
    sampleSizeElement.role = 'alert';
    sampleSizeElement.innerHTML = `Estimated number of ballots to audit: <b>${sampleSize}</b>`;
    ballotContainerDiv.appendChild(sampleSizeElement);
}

export function transitionToAuditComplete(message, flag) {
    const auditCompleteDiv = document.createElement('div');
    auditCompleteDiv.classList.add('alert', `alert-${flag}`, 'mt-3');
    auditCompleteDiv.role = 'alert';
    auditCompleteDiv.id = 'audit-complete-alert';
    auditCompleteDiv.innerHTML = message;

    const element = document.getElementById('ballot-container');
    if (element) {
        element.parentNode.removeChild(element);
    }

    document.getElementById('audit-container').appendChild(auditCompleteDiv);
}

export function activateAuditStatusCheckInterval(interval, session_id) {
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
                }
                // return console.log(response);
            })
            .catch((error) => {
                return console.error(error);
            });
    }, interval);
}

// =========================
// FOR TESTING PURPOSES ONLY

export function fillTestData() {
    console.log('Loading test data onload!');

    const testNumBallotsCast = 100;
    const testNumWinners = 1;

    const candidateName1 = 'John Doe';
    const candidateVote1 = 80;

    const candidateName2 = 'Howard Kane';
    const candidateVote2 = 20;

    const testRiskLimit = 5;

    if (document.getElementById('total-ballots-cast')) {
        document.getElementById('total-ballots-cast').value = testNumBallotsCast;
    }

    if (document.getElementById('num-winners')) {
        document.getElementById('num-winners').value = testNumWinners;
    }

    if(document.getElementById('candidate1')) {
        document.getElementById('candidate1').value = candidateName1;
    }

    if (document.getElementById('candidate1-votes')) {
        document.getElementById('candidate1-votes').value = candidateVote1;
    }

    if(document.getElementById('candidate2')) {
        document.getElementById('candidate2').value = candidateName2;
    }

    if (document.getElementById('candidate2-votes')) {
        document.getElementById('candidate2-votes').value = candidateVote2;
    }

    if (document.getElementById('risk-limit')) {
        document.getElementById('risk-limit').value = testRiskLimit;
    }

    if (document.getElementById('random-seed')) {
        document.getElementById('random-seed').value = "77526324277563029535";
    }

    if (document.getElementById('max-tests')) {
        document.getElementById('max-tests').value = 20;
    }
}

// FOR TESTING PURPOSES ONLY
// =========================
