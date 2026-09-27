/**
 * Vanilla JavaScript Application Controller (Phase 4 Stage 4J)
 * Coordinates tab switching, API data rendering, and evidence detail interactions.
 */

document.addEventListener("DOMContentLoaded", () => {
    initTabs();
    loadOverviewData();
    loadRiskData();
    loadComparisonData();
    loadRecommendationData();
    loadAuditData();
});

/* Tab Switching Logic */
function initTabs() {
    const navButtons = document.querySelectorAll(".nav-btn");
    const tabPanes = document.querySelectorAll(".tab-pane");

    navButtons.forEach(btn => {
        btn.addEventListener("click", () => {
            const targetTab = btn.getAttribute("data-tab");

            navButtons.forEach(b => b.classList.remove("active"));
            tabPanes.forEach(p => p.classList.remove("active"));

            btn.classList.add("active");
            const activePane = document.getElementById(`tab-${targetTab}`);
            if (activePane) activePane.classList.add("active");
        });
    });
}

/* Render Evidence Chip Helper */
function renderEvidenceChips(evidenceIds) {
    if (!evidenceIds || evidenceIds.length === 0) return '<span class="text-muted">None</span>';
    return evidenceIds.map(id => `<span class="ev-chip" onclick="openEvidenceModal('${id}')">${id}</span>`).join(" ");
}

/* TAB 1: Load Overview Data */
async function loadOverviewData() {
    const profileBody = document.getElementById("companyProfileBody");
    const recBody = document.getElementById("executiveSummaryBody");

    try {
        const profile = await API.getCompany();
        profileBody.innerHTML = `
            <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 12px; margin-bottom: 12px;">
                <div><strong>Industry:</strong> ${profile.industry}</div>
                <div><strong>Size:</strong> ${profile.company_size}</div>
                <div><strong>Headcount:</strong> ${profile.employee_count} Employees</div>
                <div><strong>Geography:</strong> ${profile.geography}</div>
            </div>
            <div><strong>Workforce Demographics:</strong></div>
            <p style="color: #4A5568; margin-top: 4px; font-size: 13px;">${profile.employee_demographics}</p>
        `;

        const rec = await API.getRecommendation();
        recBody.innerHTML = `
            <h4 style="font-size: 16px; color: #0A2540; font-weight: 700; margin-bottom: 8px;">Recommended Policy: ${rec.recommended_policy}</h4>
            <p style="color: #2D3748; font-size: 13px; margin-bottom: 12px;">${rec.recommendation_summary}</p>
            <div><strong>Supporting Evidence:</strong> ${renderEvidenceChips(rec.evidence_ids)}</div>
        `;
    } catch (err) {
        if (profileBody) profileBody.innerHTML = `<div class="badge badge-danger">Error loading company data: ${err.message}</div>`;
        if (recBody) recBody.innerHTML = `<div class="badge badge-danger">Error loading recommendation data: ${err.message}</div>`;
    }
}

/* TAB 2: Load Risk Analysis Data */
async function loadRiskData() {
    const container = document.getElementById("riskRequirementsContainer");
    try {
        const data = await API.getRequirements();
        const reqs = data.requirements || [];

        let html = '<div style="display: flex; flex-direction: column; gap: 16px;">';
        reqs.forEach(r => {
            let badgeClass = "badge-info";
            if (r.importance === "hard_requirement") badgeClass = "badge-danger";
            else if (r.importance === "important_requirement") badgeClass = "badge-warning";
            else if (r.importance === "preference") badgeClass = "badge-success";

            html += `
                <div class="card" style="padding: 20px;">
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
                        <h4 style="font-size: 15px; font-weight: 600; color: #0A2540;">${r.requirement_id}: ${r.requirement}</h4>
                        <span class="badge ${badgeClass}">${r.importance.replace('_', ' ').toUpperCase()}</span>
                    </div>
                    <p style="color: #4A5568; font-size: 13px; margin-bottom: 12px;"><strong>Rationale:</strong> ${r.rationale}</p>
                    <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 12px; font-size: 12px;">
                        <div><strong>Required Features:</strong> ${r.required_policy_features.join(', ')}</div>
                        <div><strong>Evidence Traceability:</strong> ${renderEvidenceChips(r.evidence_ids)}</div>
                    </div>
                </div>
            `;
        });
        html += '</div>';
        container.innerHTML = html;
    } catch (err) {
        container.innerHTML = `<div class="badge badge-danger">Error loading requirements: ${err.message}</div>`;
    }
}

/* TAB 3: Load Policy Comparison Table */
async function loadComparisonData() {
    const tbody = document.getElementById("comparisonTableBody");
    try {
        const matrix = await API.getPolicies();
        const policies = matrix.policies || [];

        let html = "";
        policies.forEach(p => {
            const evIds = p.requirement_matches.flatMap(m => m.evidence_ids);
            const uniqueEvIds = [...new Set(evIds)];

            html += `
                <tr>
                    <td><strong style="font-size: 16px; color: #0A2540;">#${p.overall_rank}</strong></td>
                    <td>
                        <strong>${p.insurer}</strong><br>
                        <span style="font-size: 12px; color: #718096;">${p.policy}</span>
                    </td>
                    <td><strong>${p.total_fit_score}</strong> / ${p.max_possible_score}</td>
                    <td><span class="badge badge-success">${p.percentage_score}%</span></td>
                    <td style="font-size: 12px;">${p.key_strengths.join('<br>• ')}</td>
                    <td style="font-size: 12px; color: #C53030;">${p.key_limitations.join('<br>• ')}</td>
                    <td>${renderEvidenceChips(uniqueEvIds.slice(0, 4))}</td>
                </tr>
            `;
        });
        tbody.innerHTML = html;
    } catch (err) {
        tbody.innerHTML = `<tr><td colspan="7" class="badge badge-danger">Error loading comparison table: ${err.message}</td></tr>`;
    }
}

/* TAB 4: Load Recommendation Detail */
async function loadRecommendationData() {
    const container = document.getElementById("recommendationDetailContainer");
    try {
        const rec = await API.getRecommendation();
        
        let traceHtml = "";
        rec.decision_trace.forEach(t => {
            traceHtml += `
                <div style="padding: 12px; background-color: #F8FAFC; border-left: 3px solid #00A896; border-radius: 4px; margin-bottom: 8px;">
                    <strong>Step ${t.step}: ${t.action}</strong>
                    <p style="font-size: 12px; color: #4A5568; margin-top: 2px;">${t.output}</p>
                </div>
            `;
        });

        container.innerHTML = `
            <div class="card" style="padding: 24px; margin-bottom: 24px; border-top: 4px solid #00A896;">
                <h3 style="font-size: 20px; color: #0A2540; font-weight: 700;">Recommended Option: ${rec.recommended_policy}</h3>
                <div style="display: flex; gap: 16px; margin: 12px 0 16px;">
                    <span class="badge badge-success" style="font-size: 13px;">Fit Score: ${rec.total_fit_score} / ${rec.max_possible_score} (${rec.percentage_score}%)</span>
                    <span class="badge badge-info" style="font-size: 13px;">Confidence: ${rec.confidence.toUpperCase()}</span>
                </div>
                <p style="font-size: 14px; color: #2D3748; line-height: 1.6; margin-bottom: 16px;">${rec.recommendation_summary}</p>
                <div><strong>Verified Evidence IDs:</strong> ${renderEvidenceChips(rec.evidence_ids)}</div>
            </div>

            <div class="grid-2">
                <div class="card" style="padding: 20px;">
                    <h4 style="font-size: 15px; color: #0A2540; font-weight: 600; margin-bottom: 12px;">Decision Trace Log</h4>
                    ${traceHtml}
                </div>

                <div class="card" style="padding: 20px;">
                    <h4 style="font-size: 15px; color: #0A2540; font-weight: 600; margin-bottom: 12px;">Key Strengths & Tradeoffs</h4>
                    <div style="margin-bottom: 12px;">
                        <strong style="color: #15803D;">Key Strengths:</strong>
                        <ul style="padding-left: 18px; margin-top: 4px; font-size: 12px;">
                            ${rec.key_strengths.map(s => `<li>${s}</li>`).join('')}
                        </ul>
                    </div>
                    <div>
                        <strong style="color: #C53030;">Tradeoffs & Limitations:</strong>
                        <ul style="padding-left: 18px; margin-top: 4px; font-size: 12px;">
                            ${rec.key_tradeoffs.map(t => `<li>${t}</li>`).join('')}
                        </ul>
                    </div>
                </div>
            </div>
        `;
    } catch (err) {
        container.innerHTML = `<div class="badge badge-danger">Error loading recommendation detail: ${err.message}</div>`;
    }
}

/* TAB 5: Load Audit Report Data */
async function loadAuditData() {
    const summaryBar = document.getElementById("auditSummaryBar");
    const tbody = document.getElementById("auditTableBody");

    try {
        const audit = await API.getAudit();
        
        summaryBar.innerHTML = `
            <div style="display: flex; gap: 24px; align-items: center; background-color: white; padding: 16px 24px; border-radius: 8px; border: 1px solid #E2E8F0;">
                <div><strong>Audit Summary:</strong> ${audit.audit_summary}</div>
                <div style="display: flex; gap: 12px;">
                    <span class="badge badge-success">${audit.pass_count} PASS</span>
                    <span class="badge badge-warning">${audit.review_count} REVIEW</span>
                    <span class="badge badge-danger">${audit.fail_count} FAIL</span>
                </div>
            </div>
        `;

        let html = "";
        audit.audited_claims.forEach(c => {
            let statusBadge = "badge-success";
            if (c.audit_status === "REVIEW") statusBadge = "badge-warning";
            else if (c.audit_status === "FAIL") statusBadge = "badge-danger";

            html += `
                <tr>
                    <td><code>${c.claim_id}</code></td>
                    <td><span class="badge ${statusBadge}">${c.audit_status}</span></td>
                    <td style="font-size: 12px; color: #2D3748;">${c.claim_text}</td>
                    <td style="font-size: 11px; color: #718096;">${c.source_output}</td>
                    <td>${renderEvidenceChips(c.evidence_ids)}</td>
                    <td style="font-size: 11px;">${c.audit_reason}</td>
                </tr>
            `;
        });
        tbody.innerHTML = html;
    } catch (err) {
        tbody.innerHTML = `<tr><td colspan="6" class="badge badge-danger">Error loading audit data: ${err.message}</td></tr>`;
    }
}
