
// ==================================================
// 1. HTML ESCAPING
// ==================================================

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


// ==================================================
// 2. ANALYZE OFFER
// ==================================================

async function analyzeOffer() {

    const input = document.getElementById("jobDescription");
    const result = document.getElementById("result");
    const button = document.querySelector(".analyzer-box .analyze-button");

    if (!input || !result || !button) return;

    const description = input.value.trim();

    if (!description) {
        result.textContent = "Please paste a job or internship description first.";
        result.className = "result-message error";
        return;
    }

    const originalButtonText = button.textContent;

    button.disabled = true;
    button.textContent = "Analyzing...";

    result.textContent = "TrustHire is reviewing the opportunity...";
    result.className = "result-message";

    try {

        const response = await fetch("/api/analyze", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({ description })
        });

        let data;

        try {
            data = await response.json();
        } catch {
            throw new Error("Invalid server response.");
        }

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

        const company = report.company_verification || {};
        const details = report.extracted_details || {};

        const ml = report.ml_assessment || {
            available: false,
            flagged: false,
            message: "The ML assessment was not included in the server response."
        };


        // ==================================================
        // 3. REPORT STATUS
        // ==================================================

        const displayStatus = report.status || "Analysis completed";

        const statusClass =
            displayStatus === "Review recommended"
                ? "report-status-warning"
                : displayStatus === "More information needed"
                    ? "report-status-review"
                    : "report-status-clear";

        const yesNo = value => value ? "Yes" : "No";


        // ==================================================
        // 4. REUSABLE DETAIL ROW
        // ==================================================

        function detailRow(label, value) {

            if (
                value === undefined ||
                value === null ||
                value === ""
            ) {
                return "";
            }

            return `
                <div class="verification-row">
                    <span>${escapeHTML(label)}</span>
                    <strong>${escapeHTML(value)}</strong>
                </div>
            `;
        }


        // ==================================================
        // 5. REPORT HEADER
        // ==================================================

        let html = `
            <div class="analysis-report">

                <div class="report-header ${statusClass}">
                    <p class="report-eyebrow">
                        TRUSTHIRE ANALYSIS REPORT
                    </p>

                    <h3>${escapeHTML(displayStatus)}</h3>

                    <p class="report-summary">
                        ${warnings.length}
                        rule-based warning${warnings.length === 1 ? "" : "s"} detected
                    </p>
                </div>
        `;


        // ==================================================
        // 6. WARNING SIGNS
        // ==================================================

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
                            ${escapeHTML(
                                warning.description ||
                                warning.reason ||
                                "A potential warning sign was identified."
                            )}
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
                            ${escapeHTML(
                                warning.action ||
                                "Verify this information independently."
                            )}
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
                        No specific rule-based warning signs detected.
                    </strong>

                    <p>
                        ${ml.available && ml.flagged
                            ? "The machine learning model recommends further review. Check the assessment below."
                            : "The current checks did not identify any warning signs. This does not guarantee that the opportunity is genuine."}
                    </p>

                </section>
            `;
        }


        // ==================================================
        // 7. MACHINE LEARNING ASSESSMENT
        // ==================================================

        html += `
            <section class="report-section ml-assessment">

                <h4>Machine Learning Assessment</h4>

                <strong>
                    ${ml.available
                        ? (
                            ml.flagged
                                ? "Further review recommended"
                                : "No additional ML warning"
                        )
                        : "ML assessment unavailable"}
                </strong>

                <p>
                    ${escapeHTML(
                        ml.message ||
                        "ML assessment could not be completed."
                    )}
                </p>

                <p class="verification-message">
                    Model availability:
                    ${ml.available ? "Available" : "Unavailable"}
                </p>

            </section>
        `;


        // ==================================================
        // 8. EXTRACTED OFFER DETAILS
        // ==================================================

        html += `
            <section class="report-section extracted-details">

                <h4>Extracted offer details</h4>

                ${detailRow("Job / internship role", details.role)}

                ${detailRow("Stipend mentioned", details.stipend)}

                ${detailRow("Duration mentioned", details.duration)}

                <div class="verification-row">
                    <span>Responsibilities provided</span>
                    <strong>${yesNo(details.responsibilities_provided)}</strong>
                </div>

                <p class="verification-message">
                    These details are extracted from the submitted text.
                    Their accuracy has not been independently confirmed.
                </p>

            </section>
        `;


        // ==================================================
        // 9. MISSING INFORMATION
        // ==================================================

        if (missingInfo.length > 0) {

            html += `
                <section class="report-section missing-info-section">

                    <h4>Information to clarify</h4>

                    <ul>
                        ${missingInfo.map(item => `
                            <li>${escapeHTML(item)}</li>
                        `).join("")}
                    </ul>

                </section>
            `;
        }


        // ==================================================
        // 10. COMPANY AND RECRUITER DETAILS
        // ==================================================

        html += `
            <section class="report-section company-verification">

                <h4>Company and recruiter details</h4>

                ${detailRow("Company name", company.company_name)}

                ${detailRow("Recruiter name", company.recruiter_name)}

                ${detailRow("Recruiter role", company.recruiter_role)}

                ${detailRow("Email address", company.email)}

                ${detailRow("Phone number", company.phone)}

                ${detailRow("Website", company.website)}

                ${detailRow("Registration link", company.registration_link)}

                <div class="verification-row">
                    <span>Company name mentioned</span>
                    <strong>${yesNo(company.company_name_mentioned)}</strong>
                </div>

                <div class="verification-row">
                    <span>Website reference mentioned</span>
                    <strong>${yesNo(company.website_reference_mentioned)}</strong>
                </div>

                <div class="verification-row">
                    <span>Website URL included in text</span>
                    <strong>${yesNo(company.website_url_provided)}</strong>
                </div>

                <div class="verification-row">
                    <span>Email or phone provided</span>
                    <strong>${yesNo(company.email_or_phone_provided)}</strong>
                </div>

                ${Array.isArray(company.sender_emails) &&
                    company.sender_emails.length > 0 ? `

                    <div class="verification-row">
                        <span>Email addresses detected</span>
                        <strong>
                            ${escapeHTML(company.sender_emails.join(", "))}
                        </strong>
                    </div>

                ` : ""}

                ${Array.isArray(company.provided_urls) &&
                    company.provided_urls.length > 0 ? `

                    <div class="verification-row">
                        <span>URLs detected</span>
                        <strong>
                            ${escapeHTML(company.provided_urls.join(", "))}
                        </strong>
                    </div>

                ` : ""}

                <div class="verification-row">
                    <span>Independent verification</span>
                    <strong class="verification-pending">
                        ${escapeHTML(
                            company.independent_verification ||
                            "Not performed"
                        )}
                    </strong>
                </div>

                <p class="verification-message">
                    TrustHire identifies contact and company details
                    mentioned in the submitted text. It does not independently
                    verify company identity, website ownership, recruiter
                    identity or job vacancies.
                </p>

            </section>
        `;


        // ==================================================
        // 11. VERIFICATION NOTE
        // ==================================================

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


        // ==================================================
        // 12. VERIFICATION CHECKLIST
        // ==================================================

        html += `
            <section class="report-section verification-checklist">

                <h4>Verification checklist</h4>

                <ul>
                    ${verificationSteps.map(step => `
                        <li>${escapeHTML(step)}</li>
                    `).join("")}
                </ul>

            </section>
        `;


        // ==================================================
        // 13. DISCLAIMER
        // ==================================================

        html += `
            <div class="report-disclaimer">
                ${escapeHTML(
                    report.disclaimer ||
                    "This is an automated preliminary review. Always verify opportunities independently."
                )}
            </div>

            </div>
        `;


        // ==================================================
        // 14. DISPLAY REPORT
        // ==================================================

        result.innerHTML = html;
        result.className = "result-message success";

    } catch (error) {

        console.error("TrustHire analysis error:", error);

        result.textContent =
            "Unable to connect to the server or process the response. Please try again.";

        result.className = "result-message error";

    } finally {

        button.disabled = false;
        button.textContent = originalButtonText;
    }
}
