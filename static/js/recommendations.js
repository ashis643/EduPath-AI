/* ==========================================================================
   EDUPATH AI — RECOMMENDATIONS PAGE INTERACTIVITY
   ========================================================================== */

function openExplanationModal(courseTitle, score, breakdownJson) {
    const modal = document.getElementById("recommendationModal");
    if (!modal) return;

    document.getElementById("modalCourseTitle").textContent = courseTitle;
    document.getElementById("modalMatchScore").textContent = `${score}% Match`;

    const reasonsList = document.getElementById("modalReasonsList");
    reasonsList.innerHTML = "";

    if (breakdownJson && breakdownJson.reasons) {
        breakdownJson.reasons.forEach(reason => {
            const li = document.createElement("li");
            li.style.cssText = "margin-bottom: 0.6rem; display: flex; align-items: flex-start; gap: 0.5rem;";
            li.innerHTML = `<span style="color: #10b981; font-weight: bold;">✓</span> <span>${reason}</span>`;
            reasonsList.appendChild(li);
        });
    }

    // Set breakdown score bars
    document.getElementById("barSkillGap").style.width = `${breakdownJson.skill_gap_match || 0}%`;
    document.getElementById("barCareerRel").style.width = `${breakdownJson.career_relevance || 0}%`;
    document.getElementById("barInterest").style.width = `${breakdownJson.interest_match || 0}%`;
    document.getElementById("barDifficulty").style.width = `${breakdownJson.difficulty_fit || 0}%`;

    modal.style.display = "flex";
}

function closeExplanationModal() {
    const modal = document.getElementById("recommendationModal");
    if (modal) modal.style.display = "none";
}

window.onclick = function(event) {
    const modal = document.getElementById("recommendationModal");
    if (event.target == modal) {
        modal.style.display = "none";
    }
};
