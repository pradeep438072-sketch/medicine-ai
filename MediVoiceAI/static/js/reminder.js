/**
 * MediVoice AI - Smart Reminder & Voice Notification Engine
 */

let activeReminders = [];
let triggeredReminders = new Set();
let reminderAudio = null;

document.addEventListener("DOMContentLoaded", () => {
    initReminderAudio();
    loadTodayReminders();
    // Check reminders every 5 seconds
    setInterval(checkRemindersSchedule, 5000);
});

function initReminderAudio() {
    reminderAudio = new Audio("/static/sounds/reminder.mp3");
    // Fallback to wav if mp3 not loaded
    reminderAudio.onerror = () => {
        reminderAudio = new Audio("/static/sounds/reminder.wav");
    };
}

/**
 * Fetch today's schedule from API
 */
async function loadTodayReminders() {
    try {
        const res = await fetch("/api/reminders/today");
        if (!res.ok) return;
        const data = await res.json();
        activeReminders = data.reminders || [];
    } catch (e) {
        console.warn("Could not fetch reminders:", e);
    }
}

/**
 * Format current time to 12-hour AM/PM (e.g. "08:00 AM")
 */
function getCurrent12HourTime() {
    const now = new Date();
    let hours = now.getHours();
    const minutes = String(now.getMinutes()).padStart(2, "0");
    const ampm = hours >= 12 ? "PM" : "AM";
    hours = hours % 12;
    hours = hours ? hours : 12;
    const hoursStr = String(hours).padStart(2, "0");
    return `${hoursStr}:${minutes} ${ampm}`;
}

/**
 * Continuously compare current time against scheduled reminder times
 */
function checkRemindersSchedule() {
    const currentTimeStr = getCurrent12HourTime(); // e.g. "08:30 AM"

    activeReminders.forEach(reminder => {
        if (reminder.status !== "pending") return;

        // The reminder_time can be single "08:00 AM" or comma-separated "08:00 AM, 02:00 PM"
        const times = reminder.reminder_time.split(",").map(t => t.trim().toUpperCase());
        const matchTime = times.find(t => t === currentTimeStr);

        const reminderKey = `${reminder.id}_${currentTimeStr}`;
        if (matchTime && !triggeredReminders.has(reminderKey)) {
            triggeredReminders.add(reminderKey);
            triggerMedicineReminder(reminder, currentTimeStr);
        }
    });
}

/**
 * Trigger sound, voice announcement, and in-app modal
 */
function triggerMedicineReminder(reminder, timeStr) {
    // 1. Play audio chime
    if (reminderAudio) {
        reminderAudio.play().catch(e => console.log("Audio autoplay prevented:", e));
    }

    // 2. Voice announcement via SpeechSynthesis
    const announcementText = `Reminder: It is time to take ${reminder.name}. Dosage: ${reminder.dosage_amount} ${reminder.dosage_unit}.`;
    speakVoiceReminder(announcementText);

    // 3. Display in-app visual modal / toast
    displayReminderModal(reminder, timeStr, announcementText);
}

/**
 * Speaks text using Web Speech API
 */
function speakVoiceReminder(text) {
    if ("speechSynthesis" in window) {
        window.speechSynthesis.cancel(); // cancel pending speech
        const utterance = new SpeechSynthesisUtterance(text);
        utterance.rate = 0.95;
        utterance.pitch = 1.0;
        utterance.volume = 1.0;
        
        // Pick high-quality English voice if available
        const voices = window.speechSynthesis.getVoices();
        const enVoice = voices.find(v => v.lang.startsWith("en") && !v.name.includes("whisper"));
        if (enVoice) utterance.voice = enVoice;

        window.speechSynthesis.speak(utterance);
    }
}

/**
 * Shows interactive Modal to mark Taken, Skipped, or Pending
 */
function displayReminderModal(reminder, timeStr, message) {
    let modalElem = document.getElementById("reminder-modal");
    if (!modalElem) {
        modalElem = document.createElement("div");
        modalElem.id = "reminder-modal";
        modalElem.className = "modal fade";
        modalElem.tabIndex = -1;
        modalElem.innerHTML = `
            <div class="modal-dialog modal-dialog-centered">
                <div class="modal-content shadow-lg border-0" style="border-radius: 20px;">
                    <div class="modal-header bg-primary text-white border-0 py-3" style="border-radius: 20px 20px 0 0;">
                        <h5 class="modal-title fw-bold">
                            <span class="brand-icon bg-white text-primary me-2">🔔</span>
                            Medicine Reminder
                        </h5>
                        <button type="button" class="btn-close btn-close-white" data-bs-dismiss="modal"></button>
                    </div>
                    <div class="modal-body text-center p-4">
                        <div class="badge bg-light text-primary px-3 py-2 rounded-pill fs-6 mb-3" id="rem-modal-time"></div>
                        <h3 class="fw-bold text-dark mb-1" id="rem-modal-name"></h3>
                        <p class="fs-5 text-muted mb-2">Dosage: <strong class="text-primary" id="rem-modal-dosage"></strong></p>
                        <p class="small text-secondary mb-4" id="rem-modal-notes"></p>
                        <div class="d-flex justify-content-center gap-2">
                            <button class="btn btn-success px-4 py-2 fw-semibold" id="btn-modal-take">
                                ✓ Mark Taken
                            </button>
                            <button class="btn btn-outline-danger px-3 py-2 fw-semibold" id="btn-modal-skip">
                                ✕ Skip
                            </button>
                            <button class="btn btn-outline-secondary px-3 py-2" data-bs-dismiss="modal">
                                ⏱ Remind Later
                            </button>
                        </div>
                    </div>
                </div>
            </div>
        `;
        document.body.appendChild(modalElem);
    }

    document.getElementById("rem-modal-time").textContent = `Scheduled for ${timeStr}`;
    document.getElementById("rem-modal-name").textContent = reminder.name;
    document.getElementById("rem-modal-dosage").textContent = `${reminder.dosage_amount} ${reminder.dosage_unit}`;
    document.getElementById("rem-modal-notes").textContent = reminder.notes || "Take as instructed.";

    const takeBtn = document.getElementById("btn-modal-take");
    const skipBtn = document.getElementById("btn-modal-skip");

    const bsModal = new bootstrap.Modal(modalElem);
    bsModal.show();

    takeBtn.onclick = () => updateReminderStatus(reminder.log_id || reminder.id, "taken", bsModal);
    skipBtn.onclick = () => updateReminderStatus(reminder.log_id || reminder.id, "skipped", bsModal);
}

/**
 * Updates status via API (Taken, Skipped, Pending)
 */
async function updateReminderStatus(logOrMedId, status, modalInstance) {
    try {
        const res = await fetch(`/api/reminders/${logOrMedId}/status`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ status })
        });
        const data = await res.json();
        if (data.status === "success") {
            if (modalInstance) modalInstance.hide();
            showToast(`Medicine marked as ${status.toUpperCase()}!`, "success");
            // Reload page or refresh list
            setTimeout(() => window.location.reload(), 1000);
        } else {
            showToast(data.message || "Failed to update status", "danger");
        }
    } catch (err) {
        showToast("Error updating reminder status.", "danger");
    }
}

// Global hook for buttons in Dashboard table
window.markMedicineStatus = (id, status) => updateReminderStatus(id, status, null);
window.triggerTestReminder = (name, dosage) => {
    triggerMedicineReminder({
        id: 9999,
        name: name || "Paracetamol",
        dosage_amount: dosage || "500",
        dosage_unit: "mg",
        notes: "Take with water"
    }, getCurrent12HourTime());
};
