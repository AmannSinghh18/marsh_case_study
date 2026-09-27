/**
 * Vanilla JavaScript Evidence Provenance Modal Handler (Phase 4 Stage 4J & Stage 49)
 * Fetches and displays exact canonical evidence provenance when evidence ID chips are clicked.
 */

async function openEvidenceModal(evidenceId) {
    const modal = document.getElementById("evidenceModal");
    const modalId = document.getElementById("modalEvidenceId");
    const modalHeader = document.getElementById("modalInsurerPolicy");
    const modalBody = document.getElementById("modalBody");

    modal.classList.add("active");
    modalId.textContent = `Evidence Traceability: ${evidenceId}`;
    modalHeader.textContent = "Loading canonical matrix record...";
    modalBody.innerHTML = '<div class="spinner">Fetching canonical provenance...</div>';

    try {
        const ev = await API.getEvidenceDetail(evidenceId);
        
        modalHeader.textContent = `${ev.insurer} — ${ev.policy} (${ev.variant || 'Standard'})`;

        modalBody.innerHTML = `
            <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 12px; margin-bottom: 16px;">
                <div><strong>Category:</strong> ${ev.category}</div>
                <div><strong>Feature:</strong> ${ev.feature}</div>
                <div><strong>Claim Type:</strong> <span class="badge badge-info">${ev.claim_type}</span></div>
                <div><strong>Review Status:</strong> <span class="badge badge-success">${ev.review_status}</span></div>
            </div>

            <div style="margin-bottom: 12px;">
                <strong>Structured Claim Statement:</strong>
                <p style="margin-top: 4px; color: #2D3748;">${ev.claim}</p>
            </div>

            <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 12px; margin-bottom: 16px;">
                <div><strong>Value / Multiplier:</strong> ${ev.value || 'N/A'}</div>
                <div><strong>Waiting Period:</strong> ${ev.waiting_period || 'N/A'}</div>
                <div><strong>Conditions:</strong> ${ev.conditions || 'None'}</div>
                <div><strong>Limitations:</strong> ${ev.limitations || 'None'}</div>
            </div>

            <div class="provenance-block">
                <div style="font-size: 11px; font-weight: 700; color: #00A896; margin-bottom: 6px;">
                    EXACT VERBATIM SOURCE PROVENANCE
                </div>
                <div style="font-size: 12px; color: #718096; margin-bottom: 8px;">
                    Document: <strong>${ev.source_document}</strong> | Page: <strong>${ev.source_page}</strong> | Section: <strong>${ev.source_section}</strong>
                </div>
                <div class="provenance-text">
                    "${ev.source_text}"
                </div>
            </div>
        `;
    } catch (err) {
        modalBody.innerHTML = `<div class="badge badge-danger">Failed to load evidence detail: ${err.message}</div>`;
    }
}

function closeEvidenceModal() {
    const modal = document.getElementById("evidenceModal");
    modal.classList.remove("active");
}

document.addEventListener("DOMContentLoaded", () => {
    const closeBtn = document.getElementById("modalCloseBtn");
    const modal = document.getElementById("evidenceModal");

    if (closeBtn) {
        closeBtn.addEventListener("click", closeEvidenceModal);
    }
    if (modal) {
        modal.addEventListener("click", (e) => {
            if (e.target === modal) closeEvidenceModal();
        });
    }
});
