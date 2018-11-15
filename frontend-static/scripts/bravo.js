let numBravoCandidates = 2; // default to 2 candidates
let ballotSequenceNumber = 1;

document.getElementById('add-candidate').addEventListener('click', () => {
    numBravoCandidates++;
    addCandidate();
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

function addCandidate() {
    const newCandidate = document.createElement('div');
    newCandidate.className = 'form-row';
    // eslint-disable-next-line
    newCandidate.innerHTML = `\
    <div class="col-md-4 mb-3">\
        <label for="candidate${numBravoCandidates}">Candidate ${numBravoCandidates} name</label>\
        <input type="text" class="form-control" id="candidate${numBravoCandidates}" placeholder="Name">\
    </div>\
    <div class="col-md-3 mb-3">\
        <label for="candidate${numBravoCandidates}-votes">Candidate ${numBravoCandidates} votes</label>\
        <input type="number" class="form-control" id="candidate${numBravoCandidates}-votes" placeholder="0" min="0">\
    </div>`;
    document.getElementById('candidates-container').appendChild(newCandidate);
}

function removeCandidate() {
    const candidates = document.querySelectorAll('#candidates-container .form-row');
    const lastCandidate = candidates[candidates.length - 1];
    if (lastCandidate) {
        document.getElementById('candidates-container').removeChild(lastCandidate);
    }
}

function getCandidateNames() {
    const candidateNameNodes = document.querySelectorAll('#candidates-container input[type="text"]');
    const candidateNames = [];
    for (const node of candidateNameNodes) {
        candidateNames.push(node.value);
    }
    return candidateNames;
}

function getCandidateVotes() {
    const candidateVoteNodes = document.querySelectorAll('#candidates-container input[type="number"]');
    const candidateVotes = [];
    // TODO: do some sort of validation to check if candidate name or votes are invalid. done on backend?
    for (const node of candidateVoteNodes) {
        candidateVotes.push(parseInt(node.value, 10));
    }
    return candidateVotes;
}

function beginBravoAudit() {
    // Remove error div if it exists
    const validationErrors = document.querySelectorAll('.validation-error');
    if (validationErrors.length > 0) {
        for (const errorNode of validationErrors) {
            errorNode.parentNode.removeChild(errorNode);
        }
    }

    // Obtain data from form
    const candidateVotes = getCandidateVotes();

    const numBallotsCast = document.getElementById('total-ballots-cast').value;
    const numWinners = document.getElementById('num-winners').value;
    const riskLimit = document.getElementById('risk-limit').value;
    const randomSeed = document.getElementById('random-seed').value;

    const totalVotesCast = candidateVotes.reduce((a, b) => a + b, 0);
    if (totalVotesCast > numBallotsCast) {
        const errorDiv = document.createElement('div');
        errorDiv.classList.add('alert', 'alert-danger', 'validation-error', 'mt-3');
        errorDiv.role = 'alert';
        errorDiv.innerHTML = 'Candidate votes are greater than the total number of votes. Please correct this and try again.';

        document.getElementById('audit-info').appendChild(errorDiv);
        return;
    }

    if (randomSeed.length < 20) {
        const errorDiv = document.createElement('div');
        errorDiv.classList.add('alert', 'alert-danger', 'validation-error', 'mt-3');
        errorDiv.role = 'alert';
        errorDiv.innerHTML = 'Random seed does not meet minimum length requirements. Please input a random seed of length 20 or greater.';

        document.getElementById('audit-info').appendChild(errorDiv);
        return;
    }

    // Setup API call
    const API_ENDPOINT = `${API_ROOT}/perform_audit`
    const formData = new FormData();

    formData.append('audit-type', 'bravo');
    formData.append('candidate-votes', JSON.stringify(candidateVotes));
    formData.append('num-ballots-cast', numBallotsCast);
    formData.append('num-winners', numWinners);
    formData.append('risk-limit', riskLimit);
    formData.append('random-seed', randomSeed);

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

            continueAudit(Math.floor((Math.random() * 1000) + 1));
            return console.log(response);
        })
        .catch((error) => {
            return console.error(error);
        });
}

// Clean up UI to remove certain buttons and disable input boxes to not mess with audit
function transitionInterfaceToInProgress() {
    // Disable text inputs
    const auditInputs = document.querySelectorAll("#audit-info input");
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
    document.getElementById("ballot-container").appendChild(sectionTitle);

    // Get estimates sample size
    // TODO: get this from the API
    const sampleSize = Math.floor((Math.random() * 100) + 1);
    const sampleSizeElement = document.createElement('div');
    sampleSizeElement.classList.add('alert', 'alert-info', 'd-inline-block');
    sampleSizeElement.role = 'alert';
    sampleSizeElement.innerHTML = `Estimated number of ballots to audit: <b>${sampleSize}</b>`;
    document.getElementById("ballot-container").appendChild(sampleSizeElement);

    // Add continue button
    const continueButton = document.createElement('button');
    continueButton.type = 'button';
    continueButton.classList.add('btn', 'btn-success');
    continueButton.id = 'continue-bravo';
    continueButton.innerHTML = 'Continue audit';
    document.getElementById('form-container').appendChild(continueButton);

    // Add event listener to continue button
    document.getElementById('continue-bravo').addEventListener('click', () => {
        getNextBallotToAudit(); // make request
        // continueAudit(Math.floor((Math.random() * 1000) + 1)); // load next ballot into DOM
    });
}

function getNextBallotToAudit() {
    // Cannot continue until next ballot to audit is returned from the back-end API
    document.getElementById('continue-bravo').setAttribute('disabled', '');

    // const API_ENDPOINT = `${API_ROOT}/perform_audit`
    // const formData = new FormData();

    const voteNodes = document.querySelectorAll('#ballot-container .form-row');
    if (voteNodes.length == 0) {
        return console.error("voteNodes is empty in the Audit section. I am sad.");
    }
    const latestVoteCheckBoxes = voteNodes[voteNodes.length - 1].getElementsByTagName('input');

    const votes = [];
    for (let i = 0; i < latestVoteCheckBoxes.length; ++i) {
        if (latestVoteCheckBoxes[i].checked) {
            votes.push(i);
        }
    }

    console.log("Vote data:", votes);

    // Remove checkbox container to load new one
    const ballotToRecordRow = document.getElementById('ballot-to-record');
    ballotToRecordRow.parentNode.removeChild(ballotToRecordRow);

    continueAudit(Math.floor((Math.random() * 1000) + 1)); // load next ballot into DOM
    document.getElementById('continue-bravo').removeAttribute('disabled');


    // formData.append('latest-ballot-votes', JSON.stringify(votes));
    // // formData.append('session', __SOME__KEY__);

    // // Make API call
    // axios.post(API_ENDPOINT, formData, {
    //     headers: {
    //         'Content-Type': 'multipart/form-data',
    //     }
    // })
    // .then((response) => {
    //     continueAudit(Math.floor((Math.random() * 1000) + 1)); // load next ballot into DOM
    //     // Re-enable the button
    //     document.getElementById('continue-bravo').removeAttribute('disabled');

    //     // TODO: use response to extract the next ballot to audit and pass it into continueAudit function below
    //     return console.log(response);
    // })
    // .catch((error) => {
    //     return console.error(error);
    // });
}

// Tell the user which ballot to cast and record.
function continueAudit(ballotNumToAudit) {
    // once audit is begun, we should change status to "Continue" and move button below
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
    document.getElementById("ballot-container").appendChild(newBallot);
}

// =========================
// FOR TESTING PURPOSES ONLY

document.onload = fillTestData();

function fillTestData() {
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
}

// FOR TESTING PURPOSES ONLY
// =========================