function updateResults(data) {
    let statusElem = document.getElementById('certStatus');
    
    if (data.success) {
        document.getElementById('learnerName').innerText = data.learner_name;
        document.getElementById('courseName').innerText = data.course_name;
        document.getElementById('platformName').innerText = data.platform;
        document.getElementById('issueDate').innerText = data.issue_date;
        document.getElementById('certId').innerText = data.cert_id;
        
        statusElem.innerHTML = '✓ ' + data.status;
        statusElem.className = 'status-badge status-valid';
    } else {
        document.getElementById('learnerName').innerText = '—';
        document.getElementById('courseName').innerText = '—';
        document.getElementById('platformName').innerText = '—';
        document.getElementById('issueDate').innerText = '—';
        document.getElementById('certId').innerText = '—';
        
        statusElem.innerHTML = '✕ ' + (data.error || 'Certificate not found');
        statusElem.className = 'status-badge status-invalid';
    }
}

async function verifyUdemy() {
    let certId = document.getElementById('udemyInput').value;
    let response = await fetch('/api/verify-udemy', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ cert_id: certId })
    });
    let data = await response.json();
    updateResults(data);
}

async function verifyCoursera() {
    let certId = document.getElementById('courseraInput').value;
    let response = await fetch('/api/verify-coursera', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ cert_id: certId })
    });
    let data = await response.json();
    updateResults(data);
}

async function verifyEdx() {
    let certId = document.getElementById('edxInput').value;
    let response = await fetch('/api/verify-edx', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ cert_id: certId })
    });
    let data = await response.json();
    updateResults(data);
}

async function verifyFreeCodeCamp() {
    let url = document.getElementById('freecodecampInput').value;
    let response = await fetch('/api/verify-freecodecamp', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ url: url })
    });
    let data = await response.json();
    updateResults(data);
}

async function verifyCs50() {
    let url = document.getElementById('cs50Input').value;
    let response = await fetch('/api/verify-cs50', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ url: url })
    });
    let data = await response.json();
    updateResults(data);
}
