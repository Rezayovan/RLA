let numBravoCandidates = 2; // default to 2 candidates

document.getElementById("add-candidate").addEventListener("click", () => {
    numBravoCandidates++;
    addCandidate();
});

document.getElementById("remove-candidate").addEventListener("click", () => {
    const candidates = document.querySelectorAll("#candidates-container .form-row");
    if (!candidates.length) return;

    numBravoCandidates--;
    removeCandidate();
});

function addCandidate() {
    const newCandidate = document.createElement("div");
    newCandidate.className = "form-row";
    // eslint-disable-next-line
    newCandidate.innerHTML = `\
    <div class="col-md-4 mb-3">\
    <label for="candidate${numBravoCandidates}">Candidate ${numBravoCandidates} name</label>\
    <input type="text" class="form-control" id="candidate${numBravoCandidates}" placeholder="Name">\
    </div>\
    <div class="col-md-4 mb-3">\
        <label for="candidate${numBravoCandidates}-votes">Candidate ${numBravoCandidates} votes</label>\
        <input type="number" class="form-control" id="candidate${numBravoCandidates}-votes" placeholder="0" min="0">\
    </div>`;
    document.getElementById("candidates-container").appendChild(newCandidate);
}

function removeCandidate() {
    const candidates = document.querySelectorAll("#candidates-container .form-row");
    const lastCandidate = candidates[candidates.length - 1];
    if (lastCandidate) {
        document.getElementById("candidates-container").removeChild(lastCandidate);
    }
}
