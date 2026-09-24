/**
 * MediVoice AI - Main JavaScript & Live Clock Engine
 */

document.addEventListener("DOMContentLoaded", () => {
    initLiveClock();
});

/**
 * Initializes and continuously updates the 12-hour AM/PM real-time clock.
 */
function initLiveClock() {
    const timeElem = document.getElementById("live-time-display");
    const ampmElem = document.getElementById("live-ampm-display");
    const dateElem = document.getElementById("live-date-display");

    function update() {
        const now = new Date();
        let hours = now.getHours();
        const minutes = String(now.getMinutes()).padStart(2, "0");
        const seconds = String(now.getSeconds()).padStart(2, "0");
        const ampm = hours >= 12 ? "PM" : "AM";

        hours = hours % 12;
        hours = hours ? hours : 12; // 0 should be 12
        const hoursStr = String(hours).padStart(2, "0");

        if (timeElem) {
            timeElem.textContent = `${hoursStr}:${minutes}:${seconds}`;
        }
        if (ampmElem) {
            ampmElem.textContent = ampm;
        }
        if (dateElem) {
            const options = { weekday: "long", year: "numeric", month: "long", day: "numeric" };
            dateElem.textContent = now.toLocaleDateString("en-US", options);
        }
    }

    update();
    setInterval(update, 1000);
}

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
