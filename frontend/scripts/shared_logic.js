export const  API_ROOT = 'http://127.0.0.1:5000'

export function addCandidate(numCandidates) {
    const newCandidate = document.createElement('div');
    newCandidate.className = 'form-row';
    newCandidate.innerHTML = `\
    <div class="col-md-4 mb-3">\
        <label for="candidate${numCandidates}">Candidate ${numCandidates} name</label>\
        <input type="text" class="form-control" id="candidate${numCandidates}" placeholder="Name">\
    </div>\
    <div class="col-md-4 mb-3">\
        <label for="candidate${numCandidates}-votes">Candidate ${numCandidates} votes</label>\
        <input type="number" class="form-control" id="candidate${numCandidates}-votes" placeholder="0" min="0">\
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
    const candidateNameNodes = document.querySelectorAll('#candidates-container input[type="text"]');
    const candidateNames = [];
    for (const node of candidateNameNodes) {
        candidateNames.push(node.value);
    }
    return candidateNames;
}

export function getCandidateVotes() {
    const candidateVoteNodes = document.querySelectorAll('#candidates-container input[type="number"]');
    const candidateVotes = [];
    // TODO: do some sort of validation to check if candidate name or votes are invalid. done on backend?
    for (const node of candidateVoteNodes) {
        candidateVotes.push(parseInt(node.value, 10));
    }
    return candidateVotes;
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

    document.getElementById('total-ballots-cast').value = testNumBallotsCast;
    document.getElementById('num-winners').value = testNumWinners;

    document.getElementById('candidate1').value = candidateName1;
    document.getElementById('candidate1-votes').value = candidateVote1;

    document.getElementById('candidate2').value = candidateName2;
    document.getElementById('candidate2-votes').value = candidateVote2;

    document.getElementById('risk-limit').value = testRiskLimit;
    document.getElementById('random-seed').value = Math.floor(Math.random() * 1000000000000000000000);
    document.getElementById('max-tests').value = 20;
}

// FOR TESTING PURPOSES ONLY
// =========================
