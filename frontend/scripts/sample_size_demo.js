import { API_ROOT, generateErrorAlert, removeElement, clearValidationErrors } from './shared_logic.js';
import { calculate_bravo_sample_size } from './sample_size_calculations.js'

let demoStarted = false;

let totalVotes;
let v_w;
let v_l;

document.getElementById('begin-demo').addEventListener('click', () => {
    clearValidationErrors();

    const API_ENDPOINT = `${API_ROOT}/get_sample_sizes_for_open_election_data`

    const spreadsheet = document.getElementById('input-election-data');
    const officeSelection = document.getElementById('office-selector').value;
    const numWinners = 1;
    const riskLimit = Number.parseFloat(document.getElementById('risk-limit').value, 10) / 100;

    if (!spreadsheet.files[0]) {
        const errorMsg = `Please upload a CSV of Open Election data to run the demo.`;
        return generateErrorAlert('demo-container', errorMsg);
    }

    if (riskLimit <= 0 || riskLimit > 100) {
        const errorMsg = 'Risk limit must be between 1% and 100%.';
        return generateErrorAlert('demo-container', errorMsg);
    }

    const formData = new FormData();

    formData.append('election-data-spreadsheet', spreadsheet.files[0]);
    formData.append('num_winners', numWinners);
    formData.append('office', officeSelection);

    axios.post(API_ENDPOINT, formData, {
            headers: {
                'Content-Type': 'multipart/form-data',
            }
        })
        .then((response) => {
            demoStarted = true;
            document.getElementById('input-election-data').setAttribute('disabled', '');
            document.getElementById('office-selector').setAttribute('disabled', '');

            const payload = response.data;
            totalVotes = payload.total_votes;
            v_w = payload.v_w;
            v_l = payload.v_l;

            const bravo_sample_size = calculate_bravo_sample_size(totalVotes, riskLimit, v_w, v_l);

            removeElement('begin-demo');

            createSampleSizeDOM(bravo_sample_size);
        })
        .catch((error) => {
            return console.error(error);
        });
});

document.getElementById('risk-limit').addEventListener('change', () => {
    if (!demoStarted) return;

    const riskLimit = Number.parseFloat(document.getElementById('risk-limit').value, 10) / 100;


    const bravo_sample_size = calculate_bravo_sample_size(totalVotes, riskLimit, v_w, v_l);
    updateSampleSizeDOM(bravo_sample_size);
});

document.getElementById('risk-limit').addEventListener('input', function() {
    document.getElementById('riskLimitOutput').value = this.value;
});

function createSampleSizeDOM(bravo_sample_size) {
    // const sampleSizeHeader = document.createElement('h2');
    // sampleSizeHeader.classList.add('bold-title');
    // sampleSizeHeader.innerHTML = 'Initial sample size of ballots to audit';
    // document.getElementById('sample-size-container').appendChild(sampleSizeHeader);

    const adjustRiskLimitMsg = document.createElement('div');
    adjustRiskLimitMsg.classList.add('alert', 'alert-primary');
    adjustRiskLimitMsg.role = 'alert';
    adjustRiskLimitMsg.innerHTML = 'Try adjusting the risk limit to see its effect on sample size!';
    document.getElementById('sample-size-container').appendChild(adjustRiskLimitMsg);

    const bravoSampleSizeElt = document.createElement('h5');
    bravoSampleSizeElt.innerHTML = `<b>BRAVO:</b> <span id='bravo-sample-size'>${bravo_sample_size.toLocaleString()}</span>`;
    document.getElementById('sample-size-container').appendChild(bravoSampleSizeElt);
}

function updateSampleSizeDOM(bravo_sample_size) {
    document.getElementById('bravo-sample-size').innerHTML = `${bravo_sample_size.toLocaleString()}`;
}
