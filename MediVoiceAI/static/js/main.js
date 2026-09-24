/**
 * MediVoice AI - Main JavaScript & Real-Time Live Clock Engine
 * 
 * Provides:
 * - Real-time live 12-hour AM/PM clock based on user's device/local timezone
 * - Smooth per-second updates without page reload (06:45:32 PM → 06:45:33 PM)
 * - Auto-formatting of current date (e.g., September 24, 2026)
 * - Tab visibility re-sync & multi-target element updates (dashboard & navbar)
 * - Toast notification manager
 */

// Global interval tracking to prevent duplicate timers
window._liveClockIntervalId = window._liveClockIntervalId || null;

/**
 * Updates all clock and date elements across the page with current local time.
 */
function updateLiveClock() {
    try {
        const now = new Date(); // Client local device time & timezone

        // 12-hour format calculation
        let rawHours = now.getHours();
        const ampm = rawHours >= 12 ? "PM" : "AM";
        let displayHours = rawHours % 12;
        displayHours = displayHours ? displayHours : 12; // 0 becomes 12

        const hoursStr = String(displayHours).padStart(2, "0");
        const minutesStr = String(now.getMinutes()).padStart(2, "0");
        const secondsStr = String(now.getSeconds()).padStart(2, "0");

        const timeStr = `${hoursStr}:${minutesStr}:${secondsStr}`;
        const fullTimeStr = `${hoursStr}:${minutesStr}:${secondsStr} ${ampm}`;

        // Date format: e.g. "September 24, 2026"
        const dateStr = now.toLocaleDateString("en-US", {
            month: "long",
            day: "numeric",
            year: "numeric"
        });

        // 1. Update all Time elements (e.g., "06:45:32")
        const timeTargets = new Set([
            ...document.querySelectorAll(".live-clock-time"),
            document.getElementById("live-time-display"),
            document.getElementById("nav-time-display")
        ]);
        timeTargets.forEach(el => {
            if (el && el.textContent !== timeStr) {
                el.textContent = timeStr;
            }
        });

        // 2. Update all AM/PM elements (e.g., "PM")
        const ampmTargets = new Set([
            ...document.querySelectorAll(".live-clock-ampm"),
            document.getElementById("live-ampm-display"),
            document.getElementById("nav-ampm-display")
        ]);
        ampmTargets.forEach(el => {
            if (el && el.textContent !== ampm) {
                el.textContent = ampm;
            }
        });

        // 3. Update all Full Clock elements (e.g., "06:45:32 PM")
        const fullTargets = new Set([
            ...document.querySelectorAll(".live-clock-full"),
            document.getElementById("live-clock-full")
        ]);
        fullTargets.forEach(el => {
            if (el && el.textContent !== fullTimeStr) {
                el.textContent = fullTimeStr;
            }
        });

        // 4. Update all Date elements (e.g., "September 24, 2026")
        const dateTargets = new Set([
            ...document.querySelectorAll(".live-clock-date"),
            document.getElementById("live-date-display"),
            document.getElementById("nav-date-display")
        ]);
        dateTargets.forEach(el => {
            if (el && el.textContent !== dateStr) {
                el.textContent = dateStr;
            }
        });
    } catch (err) {
        console.error("Error updating live clock:", err);
    }
}

/**
 * Initializes and continuously runs the live clock engine.
 */
function initLiveClock() {
    // Immediate initial sync
    updateLiveClock();

    // Clear existing interval if already initialized
    if (window._liveClockIntervalId) {
        clearInterval(window._liveClockIntervalId);
    }

    // Tick every second (1000ms)
    window._liveClockIntervalId = setInterval(updateLiveClock, 1000);
}

// Expose globally
window.updateLiveClock = updateLiveClock;
window.initLiveClock = initLiveClock;

// Auto-run on DOMContentLoaded or immediately if already loaded
if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", initLiveClock);
} else {
    initLiveClock();
}

// Re-sync immediately when user switches back to this tab/window
document.addEventListener("visibilitychange", () => {
    if (!document.hidden) {
        updateLiveClock();
    }
});

/**
 * Helper to show toast messages.
 */
function showToast(message, type = "info") {
    const toastContainer = document.getElementById("toast-container") || createToastContainer();
    const toast = document.createElement("div");
    toast.className = `alert alert-${type} shadow-sm fade show mb-2`;
    toast.style.minWidth = "260px";
    toast.role = "alert";
    toast.innerHTML = `
        <div class="d-flex justify-content-between align-items-center">
            <span>${message}</span>
            <button type="button" class="btn-close ms-2" data-bs-dismiss="alert" aria-label="Close"></button>
        </div>
    `;
    toastContainer.appendChild(toast);
    setTimeout(() => {
        toast.classList.remove("show");
        setTimeout(() => toast.remove(), 300);
    }, 4000);
}

function createToastContainer() {
    const div = document.createElement("div");
    div.id = "toast-container";
    div.className = "position-fixed bottom-0 end-0 p-3";
    div.style.zIndex = "9999";
    document.body.appendChild(div);
    return div;
}
