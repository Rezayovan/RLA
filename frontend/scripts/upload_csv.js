document.getElementById('upload-election-data').addEventListener('click', () => {
    const API_ENDPOINT = `${API_ROOT}/upload_open_election_data`
    let formData = new FormData();
    let spreadsheet = document.getElementById('input-election-data');
    formData.append('election-data-spreadsheet', spreadsheet.files[0]);
    axios.post(API_ENDPOINT, formData, {
            headers: {
                'Content-Type': 'multipart/form-data',
            }
        })
        .then((response) => {
            return console.log(response);
        })
        .catch((error) => {
            return console.error(error);
        });
});