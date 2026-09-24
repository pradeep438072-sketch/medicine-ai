/**
 * MediVoice AI - Voice Assistant Client
 */

let recognition = null;
let isListening = false;

document.addEventListener("DOMContentLoaded", () => {
    initSpeechRecognition();
    initVoiceControls();
});

function initSpeechRecognition() {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (SpeechRecognition) {
        recognition = new SpeechRecognition();
        recognition.continuous = false;
        recognition.interimResults = false;
        recognition.lang = "en-US";

        recognition.onstart = () => {
            isListening = true;
            updateMicUI(true);
            updateStatusText("Listening... Speak your command now");
        };

        recognition.onresult = (event) => {
            const transcript = event.results[0][0].transcript;
            addChatMessage(transcript, "user");
            sendVoiceCommand(transcript);
        };

        recognition.onerror = (event) => {
            console.warn("Speech recognition error:", event.error);
            isListening = false;
            updateMicUI(false);
            updateStatusText("Microphone idle. Click to speak or type below.");
        };

        recognition.onend = () => {
            isListening = false;
            updateMicUI(false);
            updateStatusText("Microphone idle. Click to speak or type below.");
        };
    } else {
        console.warn("Speech recognition not supported in this browser.");
        updateStatusText("Speech recognition not supported in browser. Use text input below.");
    }
}

function initVoiceControls() {
    const micBtn = document.getElementById("mic-assistant-btn");
    const textForm = document.getElementById("voice-text-form");
    const textInput = document.getElementById("voice-text-input");

    if (micBtn) {
        micBtn.addEventListener("click", toggleListening);
    }

    if (textForm) {
        textForm.addEventListener("submit", (e) => {
            e.preventDefault();
            const text = textInput.value.trim();
            if (!text) return;
            textInput.value = "";
            addChatMessage(text, "user");
            sendVoiceCommand(text);
        });
    }

    // Quick Command Pills
    document.querySelectorAll(".quick-command-pill").forEach(pill => {
        pill.addEventListener("click", () => {
            const command = pill.getAttribute("data-command");
            addChatMessage(command, "user");
            sendVoiceCommand(command);
        });
    });
}

function toggleListening() {
    if (!recognition) {
        showToast("Voice recognition is not supported in this browser. Please type your command.", "info");
        return;
    }

    if (isListening) {
        recognition.stop();
    } else {
        try {
            recognition.start();
        } catch (e) {
            console.error("Recognition start error:", e);
        }
    }
}

function updateMicUI(listening) {
    const micBtn = document.getElementById("mic-assistant-btn");
    const waveElem = document.getElementById("voice-wave-animation");
    if (!micBtn) return;

    if (listening) {
        micBtn.classList.add("recording");
        if (waveElem) waveElem.classList.remove("d-none");
    } else {
        micBtn.classList.remove("recording");
        if (waveElem) waveElem.classList.add("d-none");
    }
}

function updateStatusText(txt) {
    const elem = document.getElementById("assistant-status");
    if (elem) elem.textContent = txt;
}

/**
 * Send transcribed voice or text to backend Python Voice Assistant
 */
async function sendVoiceCommand(commandText) {
    updateStatusText("Processing with MediVoice AI...");

    try {
        const res = await fetch("/api/voice/command", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ command: commandText })
        });
        const data = await res.json();

        // 1. Add assistant bubble
        addChatMessage(data.text, "assistant");

        // 2. Speak response aloud
        speakText(data.spoken || data.text);

        // 3. Handle actions (navigation, reminder triggers)
        if (data.action === "navigate" && data.url) {
            setTimeout(() => {
                window.location.href = data.url;
            }, 1800);
        } else if (data.action === "trigger_reminder" && data.medicine) {
            if (window.triggerMedicineReminder) {
                window.triggerMedicineReminder(data.medicine, "Now");
            }
        }

        updateStatusText("Ready for your next question.");
    } catch (err) {
        console.error("Voice command error:", err);
        addChatMessage("I'm sorry, I could not process your voice command right now.", "assistant");
        updateStatusText("Error processing command.");
    }
}

function addChatMessage(message, sender = "user") {
    const transcript = document.getElementById("assistant-chat-transcript");
    if (!transcript) return;

    const div = document.createElement("div");
    div.className = `d-flex mb-3 ${sender === "user" ? "justify-content-end" : "justify-content-start"}`;

    if (sender === "user") {
        div.innerHTML = `
            <div class="p-3 bg-primary text-white rounded-4 shadow-sm" style="max-width: 80%;">
                <small class="d-block fw-semibold opacity-75 mb-1">You</small>
                <span>${message}</span>
            </div>
        `;
    } else {
        div.innerHTML = `
            <div class="p-3 bg-white border rounded-4 shadow-sm text-dark" style="max-width: 80%;">
                <div class="d-flex align-items-center mb-1">
                    <span class="badge bg-primary-subtle text-primary me-2">MediVoice AI</span>
                    <button class="btn btn-sm btn-link p-0 text-decoration-none" onclick="speakText('${message.replace(/'/g, "\\'")}')">🔊 Replay</button>
                </div>
                <span>${message}</span>
            </div>
        `;
    }

    transcript.appendChild(div);
    transcript.scrollTop = transcript.scrollHeight;
}

function speakText(text) {
    if ("speechSynthesis" in window) {
        window.speechSynthesis.cancel();
        const utterance = new SpeechSynthesisUtterance(text);
        utterance.rate = 1.0;
        utterance.pitch = 1.0;
        window.speechSynthesis.speak(utterance);
    }
}
