/* ==========================================================================
   EDUPATH AI — MAIN INTERACTIVITY & AJAX HELPERS
   ========================================================================== */

document.addEventListener("DOMContentLoaded", () => {
    console.log("EduPath AI Core JS Loaded.");
});

/**
 * Updates a student's course status dynamically via REST API
 * @param {number} courseId 
 * @param {string} status ('in_progress', 'completed', 'saved')
 * @param {number} progressPct 
 */
async function updateCourseStatus(courseId, status, progressPct = 0) {
    try {
        const response = await fetch("/api/course/status", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({
                course_id: courseId,
                status: status,
                progress_pct: progressPct
            })
        });

        const data = await response.json();
        if (data.success) {
            showToast(data.message, "success");
            setTimeout(() => {
                window.location.reload();
            }, 800);
        } else {
            showToast(data.message || "Failed to update course status.", "danger");
        }
    } catch (err) {
        console.error("Status update error:", err);
        showToast("Error connecting to server.", "danger");
    }
}

/**
 * Toast Notification Utility
 */
function showToast(message, type = "info") {
    let container = document.getElementById("toast-container");
    if (!container) {
        container = document.createElement("div");
        container.id = "toast-container";
        container.style.cssText = "position: fixed; bottom: 20px; right: 20px; z-index: 9999; display: flex; flex-direction: column; gap: 10px;";
        document.body.appendChild(container);
    }

    const toast = document.createElement("div");
    toast.className = `alert alert-${type}`;
    toast.style.cssText = "min-width: 250px; box-shadow: 0 5px 15px rgba(0,0,0,0.5); margin: 0;";
    toast.innerHTML = `<span>${message}</span>`;

    container.appendChild(toast);
    setTimeout(() => {
        toast.remove();
    }, 4000);
}
