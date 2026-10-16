// Polished Frontend Logic for CV Matcher & LinkedIn Verification System
const API_BASE = window.location.origin;

let candidatesList = [];

// DOM Elements
const cvFileInput = document.getElementById('cvFileInput');
const dropzone = document.getElementById('dropzone');
const fileNameDisplay = document.getElementById('fileNameDisplay');
const uploadForm = document.getElementById('uploadForm');
const btnSubmit = document.getElementById('btnSubmit');
const submitSpinner = document.getElementById('submitSpinner');
const pipelineTracker = document.getElementById('pipelineTracker');

const resultPlaceholder = document.getElementById('resultPlaceholder');
const resultContent = document.getElementById('resultContent');
const matchBadge = document.getElementById('matchBadge');
const statusSummaryBox = document.getElementById('statusSummaryBox');
const statusBannerIcon = document.getElementById('statusBannerIcon');
const statusSummaryTitle = document.getElementById('statusSummaryTitle');
const statusSummaryDesc = document.getElementById('statusSummaryDesc');

const resName = document.getElementById('resName');
const resId = document.getElementById('resId');
const resEmail = document.getElementById('resEmail');
const resPhone = document.getElementById('resPhone');
const resLinkedin = document.getElementById('resLinkedin');
const resEdu = document.getElementById('resEdu');
const resExp = document.getElementById('resExp');
const resSkills = document.getElementById('resSkills');

const candidatesTableBody = document.getElementById('candidatesTableBody');
const btnRefreshTable = document.getElementById('btnRefreshTable');
const searchFilter = document.getElementById('searchFilter');

// Initialization
document.addEventListener('DOMContentLoaded', () => {
    fetchCandidates();
    setupDropzone();
});

// Drag & Drop Setup
function setupDropzone() {
    ['dragenter', 'dragover'].forEach(eventName => {
        dropzone.addEventListener(eventName, (e) => {
            e.preventDefault();
            e.stopPropagation();
            dropzone.classList.add('dragover');
        });
    });

    ['dragleave', 'drop'].forEach(eventName => {
        dropzone.addEventListener(eventName, (e) => {
            e.preventDefault();
            e.stopPropagation();
            dropzone.classList.remove('dragover');
        });
    });

    dropzone.addEventListener('drop', (e) => {
        const dt = e.dataTransfer;
        const files = dt.files;
        if (files.length > 0) {
            cvFileInput.files = files;
            updateFileNameDisplay(files[0].name);
        }
    });

    cvFileInput.addEventListener('change', (e) => {
        if (e.target.files.length > 0) {
            updateFileNameDisplay(e.target.files[0].name);
        }
    });
}

function updateFileNameDisplay(name) {
    fileNameDisplay.innerHTML = `<span style="color:#4f46e5;font-weight:700;">Selected:</span> ${escapeHtml(name)} <span style="color:#059669;font-size:0.8rem;margin-left:6px;">✓ Ready</span>`;
}

// Upload & Process CV
uploadForm.addEventListener('submit', async (e) => {
    e.preventDefault();

    if (!cvFileInput.files || cvFileInput.files.length === 0) {
        alert("Please select or drop a CV file first (PDF or DOCX).");
        return;
    }

    const file = cvFileInput.files[0];
    const formData = new FormData();
    formData.append("file", file);

    btnSubmit.disabled = true;
    submitSpinner.style.display = "inline-block";
    pipelineTracker.style.display = "flex";
    resetPipelineSteps();

    // Step tracker animations
    animatePipelineStep('step1');

    try {
        setTimeout(() => animatePipelineStep('step2'), 400);
        setTimeout(() => animatePipelineStep('step3'), 800);
        setTimeout(() => animatePipelineStep('step4'), 1200);

        const response = await fetch(`${API_BASE}/api/upload-cv`, {
            method: 'POST',
            body: formData
        });

        if (!response.ok) {
            const err = await response.json();
            throw new Error(err.detail || "Failed to process CV");
        }

        const data = await response.json();

        // Mark all steps complete
        ['step1', 'step2', 'step3', 'step4'].forEach(id => {
            const el = document.getElementById(id);
            if (el) el.className = 'pipeline-step completed';
        });

        // Display results
        renderResult(data);

        // Refresh database table
        fetchCandidates();

    } catch (err) {
        alert("Error processing CV: " + err.message);
    } finally {
        btnSubmit.disabled = false;
        submitSpinner.style.display = "none";
    }
});

function resetPipelineSteps() {
    ['step1', 'step2', 'step3', 'step4'].forEach(id => {
        const el = document.getElementById(id);
        if (el) el.className = 'pipeline-step';
    });
}

function animatePipelineStep(stepId) {
    const el = document.getElementById(stepId);
    if (el) {
        el.className = 'pipeline-step active';
    }
}

// Render Result Card
function renderResult(data) {
    resultPlaceholder.style.display = 'none';
    resultContent.style.display = 'block';

    const match = data.match_result;
    const cv = data.extracted_cv;

    // Match Status Badge & Summary Box
    if (match.status.includes('Matched')) {
        matchBadge.className = 'badge badge-matched';
        matchBadge.textContent = '✓ Matched with LinkedIn profile';
        statusSummaryBox.className = 'status-banner matched';
        statusBannerIcon.textContent = '✓';
        statusSummaryTitle.textContent = 'Matched with LinkedIn profile';
        statusSummaryDesc.textContent = match.reason || 'Candidate CV successfully validated against LinkedIn profile records.';
    } else {
        matchBadge.className = 'badge badge-mismatched';
        matchBadge.textContent = "✗ LinkedIn profile doesn't match";
        statusSummaryBox.className = 'status-banner mismatched';
        statusBannerIcon.textContent = '✗';
        statusSummaryTitle.textContent = "LinkedIn profile doesn't match";
        statusSummaryDesc.textContent = match.reason || 'Discrepancy detected between candidate CV and LinkedIn profile.';
    }

    resName.textContent = cv.name || 'N/A';
    resId.textContent = `#${data.candidate_id}`;
    resEmail.textContent = cv.email || 'N/A';
    resPhone.textContent = cv.phone || 'N/A';
    
    resLinkedin.textContent = cv.linkedin_url && cv.linkedin_url !== 'N/A' ? 'LinkedIn Profile ↗' : 'No LinkedIn Profile';
    resLinkedin.href = cv.linkedin_url && cv.linkedin_url !== 'N/A' ? cv.linkedin_url : '#';

    resEdu.textContent = cv.educational_background || 'N/A';
    resExp.textContent = cv.experiences || cv.professional_background || 'N/A';
    
    // Skills tags rendering
    const skillsList = (cv.skills || '').split(/[,|;]/).map(s => s.trim()).filter(Boolean);
    if (skillsList.length > 0) {
        resSkills.innerHTML = skillsList.map(s => `<span class="linkedin-pill-link" style="margin-right:6px;margin-bottom:6px;display:inline-block;">${escapeHtml(s)}</span>`).join('');
    } else {
        resSkills.textContent = cv.skills || 'N/A';
    }
}

// Fetch Candidates from MySQL
async function fetchCandidates() {
    try {
        const res = await fetch(`${API_BASE}/api/candidates`);
        const json = await res.json();
        if (json.success) {
            candidatesList = json.candidates || [];
            renderTable(candidatesList);
        }
    } catch (e) {
        console.error("Could not fetch candidates from database:", e);
    }
}

// Render Database Table
function renderTable(list) {
    if (!list || list.length === 0) {
        candidatesTableBody.innerHTML = `<tr><td colspan="7" class="text-center py-4 text-muted">No candidate records found in database. Upload a CV above.</td></tr>`;
        return;
    }

    candidatesTableBody.innerHTML = list.map(c => {
        const isMatch = c.match_status && c.match_status.includes('Matched');
        const badgeClass = isMatch ? 'badge-matched' : 'badge-mismatched';
        const badgeIcon = isMatch ? '✓' : '✗';
        const formattedDate = c.created_at ? new Date(c.created_at).toLocaleDateString() : '-';

        return `
            <tr>
                <td class="code-font" style="font-weight:700;">#${c.id}</td>
                <td>
                    <div class="cand-name">${escapeHtml(c.name)}</div>
                    <div class="cand-subtext">${escapeHtml(c.email || 'N/A')}${c.phone ? ' • ' + escapeHtml(c.phone) : ''}</div>
                </td>
                <td>
                    ${c.linkedin_url && c.linkedin_url !== 'N/A' 
                        ? `<a href="${c.linkedin_url}" target="_blank" class="linkedin-pill-link">Profile ↗</a>` 
                        : '<span class="text-muted" style="font-size:0.8rem;">None</span>'}
                </td>
                <td>
                    <div class="truncate-text" title="${escapeHtml(c.educational_background || '')}">
                        ${escapeHtml((c.educational_background || '').substring(0, 45))}
                    </div>
                </td>
                <td>
                    <div class="truncate-text" title="${escapeHtml(c.experiences || c.professional_background || '')}">
                        ${escapeHtml((c.experiences || c.professional_background || '').substring(0, 50))}
                    </div>
                </td>
                <td>
                    <span class="badge ${badgeClass}">${badgeIcon} ${escapeHtml(c.match_status)}</span>
                </td>
                <td style="font-size:0.8rem;color:var(--text-muted);">${formattedDate}</td>
            </tr>
        `;
    }).join('');
}

// Search Filter
searchFilter.addEventListener('input', (e) => {
    const q = e.target.value.toLowerCase();
    const filtered = candidatesList.filter(c => 
        (c.name && c.name.toLowerCase().includes(q)) ||
        (c.email && c.email.toLowerCase().includes(q)) ||
        (c.match_status && c.match_status.toLowerCase().includes(q))
    );
    renderTable(filtered);
});

btnRefreshTable.addEventListener('click', fetchCandidates);

function escapeHtml(text) {
    if (!text) return '';
    return String(text)
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#039;");
}
