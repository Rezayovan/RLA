import {
    API_ROOT,
    generateErrorAlert,
    removeElement,
    clearValidationErrors
} from './shared_logic.js';

import {
    calculate_bravo_sample_size, calculate_super_simple_sample_size
} from './calculate_sample_size.js';

const inflationRate = 1.1;
const tolerance20 = 0.2;
const tolerance50 = 0.5;

let demoStarted = false;

let totalVotes;
let v_w;
let v_l;

document.getElementById('input-election-data').addEventListener('change', function () {
    const file = this.files[0];
    if (!file) return;
    document.getElementById('input-election-data-label').innerHTML = file.name;
});

document.getElementById('begin-demo').addEventListener('click', () => {
    clearValidationErrors();

    const API_ENDPOINT = `${API_ROOT}/get_sample_sizes_for_open_election_data`

    const spreadsheet = document.getElementById('input-election-data');
    const numWinners = 1;
    let riskLimit = parseInt(document.getElementById('risk-limit').value, 10);

    if (!spreadsheet.files[0]) {
        const errorMsg = `Please upload a CSV of Open Election data to run the demo.`;
        return generateErrorAlert('demo-container', errorMsg);
    }

    if (riskLimit <= 0 || riskLimit > 100) {
        const errorMsg = 'Risk limit must be between 1% and 100%.';
        return generateErrorAlert('demo-container', errorMsg);
    }

    riskLimit = Number.parseFloat(riskLimit) / 100;

    document.getElementById('begin-demo').setAttribute('disabled', '');

    const formData = new FormData();

    formData.append('election-data-spreadsheet', spreadsheet.files[0]);
    formData.append('num_winners', numWinners);

    axios.post(API_ENDPOINT, formData, {
            headers: {
                'Content-Type': 'multipart/form-data',
            }
        })
        .then((response) => {
            demoStarted = true;
            removeElement('begin-demo');
            document.getElementById('input-election-data').setAttribute('disabled', '');

            const payload = response.data;
            totalVotes = payload.total_votes;
            v_w = payload.v_w;
            v_l = payload.v_l;
            const office_chosen = payload.office_chosen;

            const bravo_sample_size = calculate_bravo_sample_size(totalVotes, riskLimit, v_w, v_l);

            const super_simple_sample_size20 = calculate_super_simple_sample_size(totalVotes, riskLimit, v_w, v_l, inflationRate, tolerance20);
            const super_simple_sample_size50 = calculate_super_simple_sample_size(totalVotes, riskLimit, v_w, v_l, inflationRate, tolerance50);

            createSampleSizeDOM(office_chosen, bravo_sample_size, super_simple_sample_size20, super_simple_sample_size50);
        })
        .catch((error) => {
            generateErrorAlert('sample-size-container', 'Unable to parse Open Election data for the selected house. Please try another house or upload another dataset.')
            return console.error(error);
        });
});

document.getElementById('risk-limit').addEventListener('change', handleSliderChange);

document.getElementById('risk-limit').addEventListener('input', function () {
    document.getElementById('riskLimitOutput').value = this.value;
});

function handleSliderChange() {
    if (!demoStarted) return;

    const riskLimit = Number.parseFloat(document.getElementById('risk-limit').value) / 100;

    const bravo_sample_size = calculate_bravo_sample_size(totalVotes, riskLimit, v_w, v_l);

    const super_simple_sample_size20 = calculate_super_simple_sample_size(totalVotes, riskLimit, v_w, v_l, inflationRate, tolerance20);

    const super_simple_sample_size50 = calculate_super_simple_sample_size(totalVotes, riskLimit, v_w, v_l, inflationRate, tolerance50);

    updateSampleSizeDOM(bravo_sample_size, super_simple_sample_size20, super_simple_sample_size50);
}

function createSampleSizeDOM(office_chosen, bravo_sample_size, super_simple_sample_size20, super_simple_sample_size50) {
    // const sampleSizeHeader = document.createElement('h2');
    // sampleSizeHeader.innerHTML = 'Initial sample size of ballots to audit';
    // document.getElementById('sample-size-container').appendChild(sampleSizeHeader);

    const sampleSizeHeader = document.createElement('h4');
    sampleSizeHeader.innerHTML = `Office chosen for calculations: ${office_chosen}`;
    document.getElementById('sample-size-container').appendChild(sampleSizeHeader);

    const adjustRiskLimitMsg = document.createElement('div');
    adjustRiskLimitMsg.classList.add('alert', 'alert-primary');
    adjustRiskLimitMsg.role = 'alert';
    adjustRiskLimitMsg.innerHTML = 'Try adjusting the risk limit to see its effect on sample size!';
    document.getElementById('sample-size-container').appendChild(adjustRiskLimitMsg);

    const bravoSampleSizeElt = document.createElement('h4');
    bravoSampleSizeElt.innerHTML = `<b>BRAVO:</b> <span id='bravo-sample-size'>${bravo_sample_size.toLocaleString()}</span>`;
    document.getElementById('sample-size-container').appendChild(bravoSampleSizeElt);

    const superSimpleSampleSize20Elt = document.createElement('h4');
    superSimpleSampleSize20Elt.innerHTML = `<b>Super-Simple (20% tolerance):</b> <span id='super-simple-sample-size-20'>${super_simple_sample_size20.toLocaleString()}</span>`;
    document.getElementById('sample-size-container').appendChild(superSimpleSampleSize20Elt);

    const superSimpleSampleSize50Elt = document.createElement('h4');
    superSimpleSampleSize50Elt.innerHTML = `<b>Super-Simple (50% tolerance):</b> <span id='super-simple-sample-size-50'>${super_simple_sample_size50.toLocaleString()}</span>`;
    document.getElementById('sample-size-container').appendChild(superSimpleSampleSize50Elt);
}

function updateSampleSizeDOM(bravo_sample_size, super_simple_sample_size20, super_simple_sample_size50) {
    document.getElementById('bravo-sample-size').innerHTML = `${bravo_sample_size.toLocaleString()}`;
    document.getElementById('super-simple-sample-size-20').innerHTML = `${super_simple_sample_size20.toLocaleString()}`;
    document.getElementById('super-simple-sample-size-50').innerHTML = `${super_simple_sample_size50.toLocaleString()}`;
}