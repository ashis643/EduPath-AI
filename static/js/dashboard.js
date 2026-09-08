/* ==========================================================================
   EDUPATH AI — DASHBOARD CHART.JS VISUALIZATIONS
   ========================================================================== */

function initDashboardCharts(readinessPct, skillProgressData) {
    // 1. Skill Progress Bar Chart
    const ctxSkill = document.getElementById("skillChart");
    if (ctxSkill && skillProgressData && skillProgressData.length > 0) {
        const labels = skillProgressData.map(s => s.name);
        const progressValues = skillProgressData.map(s => s.progress_pct);
        const colors = skillProgressData.map(s => s.completed ? "#10b981" : (s.progress_pct > 0 ? "#3b82f6" : "#64748b"));

        new Chart(ctxSkill, {
            type: "bar",
            data: {
                labels: labels,
                datasets: [{
                    label: "Skill Progress %",
                    data: progressValues,
                    backgroundColor: colors,
                    borderRadius: 6,
                    borderSkipped: false
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { display: false },
                    tooltip: {
                        callbacks: {
                            label: function(context) {
                                return ` Progress: ${context.raw}%`;
                            }
                        }
                    }
                },
                scales: {
                    x: {
                        ticks: { color: "#94a3b8", font: { family: "Plus Jakarta Sans", size: 11 } },
                        grid: { color: "rgba(255,255,255,0.05)" }
                    },
                    y: {
                        min: 0,
                        max: 100,
                        ticks: { color: "#94a3b8", stepSize: 20 },
                        grid: { color: "rgba(255,255,255,0.05)" }
                    }
                }
            }
        });
    }

    // 2. Career Readiness Doughnut Chart
    const ctxGauge = document.getElementById("readinessGauge");
    if (ctxGauge) {
        const remaining = 100 - readinessPct;
        new Chart(ctxGauge, {
            type: "doughnut",
            data: {
                labels: ["Readiness Achieved", "Gap Remaining"],
                datasets: [{
                    data: [readinessPct, remaining],
                    backgroundColor: [
                        "rgba(99, 102, 241, 0.9)",
                        "rgba(255, 255, 255, 0.08)"
                    ],
                    borderWidth: 0,
                    hoverOffset: 4
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                cutout: "80%",
                plugins: {
                    legend: { display: false }
                }
            }
        });
    }
}
