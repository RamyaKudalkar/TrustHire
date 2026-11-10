
function escapeHTML(value) {
    return String(value ?? "").replace(/[&<>"']/g, function (character) {
        const entities = {
            "&": "&amp;",
            "<": "&lt;",
            ">": "&gt;",
            '"': "&quot;",
            "'": "&#39;"
        };

        return entities[character];
    });
}

async function analyzeOffer() {
    const input = document.getElementById("jobDescription");
    const result = document.getElementById("result");
    const button = document.querySelector(".analyzer-box button");

    if (!input || !result || !button) {
        return;
    }

    const description = input.value.trim();

    if (!description) {
        result.textContent =
            "Please paste a job or internship description first.";

        result.className = "result-message error";
        return;
    }

    button.disabled = true;
    button.textContent = "Analyzing...";

    result.textContent =
        "TrustHire is reviewing the opportunity...";

    result.className = "result-message";

    try {
        const response = await fetch("/api/analyze", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({
                description: description
            })
        });

        const data = await response.json();

        if (!response.ok) {
            result.textContent =
                data.message || "Unable to analyze this opportunity.";

            result.className = "result-message error";
            return;
        }

        if (!data.report || typeof data.report !== "object") {
            throw new Error("Invalid report received.");
        }

        const report = data.report;

        const warnings = Array.isArray(report.warnings)
            ? report.warnings
            : [];

        const missingInfo = Array.isArray(report.missing_information)
            ? report.missing_information
            : [];

        const verificationSteps = Array.isArray(report.verification_steps)
            ? report.verification_steps
            : [];

        const companyVerification =
            report.company_verification || {};

        const statusClass = warnings.length > 0
            ? "report-status-warning"
            : missingInfo.length > 0
                ? "report-status-review"
                : "report-status-clear";

        let html = `
            <div class="analysis-report">

                <div class="report-header ${statusClass}">
                    <p class="report-eyebrow">
                        TRUSTHIRE ANALYSIS REPORT
                    </p>

                    <h3>${escapeHTML(report.status || "Analysis complete")}</h3>

                    <p class="report-summary">
                        ${warnings.length}
                        warning${warnings.length === 1 ? "" : "s"} found
                    </p>
                </div>
        `;

        // Warning signs

        if (warnings.length > 0) {
            html += `
                <section class="report-section">
                    <h4>Warning signs</h4>
                    <div class="warning-list">
            `;

            warnings.forEach(warning => {
                html += `
                    <div class="result-message error warning-item">

                        <strong>
                            ${escapeHTML(warning.title)}
                        </strong>

                        <p>
                            ${escapeHTML(warning.reason)}
                        </p>

                        ${warning.evidence ? `
                            <div class="evidence-label">
                                Evidence found
                            </div>

                            <blockquote>
                                "${escapeHTML(warning.evidence)}"
                            </blockquote>
                        ` : ""}

                        <p>
                            <strong>What to do:</strong>
                            ${escapeHTML(warning.action)}
                        </p>

                    </div>
                `;
            });

            html += `
                    </div>
                </section>
            `;

        } else {
            html += `
                <section class="report-section no-warning-note">

                    <strong>
                        No obvious warning signs detected.
                    </strong>

                    <p>
                        The current checks did not identify any warning signs.
                        This does not guarantee that the opportunity is genuine.
                    </p>

                </section>
            `;
        }

        // Missing information

        if (missingInfo.length > 0) {
            html += `
                <section class="report-section missing-info-section">

                    <h4>Information to clarify</h4>

                    <ul>
            `;

            missingInfo.forEach(item => {
                html += `<li>${escapeHTML(item)}</li>`;
            });

            html += `
                    </ul>
                </section>
            `;
        }

        // Company verification

        html += `
            <section class="report-section company-verification">

                <h4>Company verification</h4>

                <div class="verification-row">
                    <span>Company name mentioned</span>

                    <strong>
                        ${companyVerification.company_name_mentioned
                            ? "Yes"
                            : "No"}
                    </strong>
                </div>

                <div class="verification-row">
                    <span>Contact information mentioned</span>

                    <strong>
                        ${companyVerification.contact_information_mentioned
                            ? "Yes"
                            : "No"}
                    </strong>
                </div>

                <div class="verification-row">
                    <span>Independent verification</span>

                    <strong class="verification-pending">
                        ${escapeHTML(
                            companyVerification.independent_verification ||
                            "Not performed"
                        )}
                    </strong>
                </div>

                <p class="verification-message">
                    ${escapeHTML(
                        companyVerification.message ||
                        "TrustHire has not independently verified the company's identity or job vacancy."
                    )}
                </p>

            </section>
        `;

        // Important verification note

        if (report.verification_note) {
            html += `
                <section class="report-section verification-note">

                    <h4>Important verification note</h4>

                    <p>
                        ${escapeHTML(report.verification_note)}
                    </p>

                </section>
            `;
        }

        // Verification checklist

        html += `
            <section class="report-section verification-checklist">

                <h4>Verification checklist</h4>

                <ul>
        `;

        verificationSteps.forEach(step => {
            html += `<li>${escapeHTML(step)}</li>`;
        });

        html += `
                </ul>
            </section>
        `;

        // Disclaimer

        html += `
            <div class="report-disclaimer">
                ${escapeHTML(
                    report.disclaimer ||
                    "This is an automated preliminary review. Always verify opportunities independently."
                )}
            </div>

            </div>
        `;

        result.innerHTML = html;
        result.className = "result-message success";

    } catch (error) {
        result.textContent =
            "Unable to connect to the server. Please try again.";

        result.className = "result-message error";

    } finally {
        button.disabled = false;
        button.textContent = "Analyze Opportunity →";
    }
}
