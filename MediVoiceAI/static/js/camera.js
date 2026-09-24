/**
 * MediVoice AI - Camera OCR & Medicine Detection Client
 */

let videoStream = null;

document.addEventListener("DOMContentLoaded", () => {
    initCameraControls();
});

function initCameraControls() {
    const videoElem = document.getElementById("camera-video");
    const startCamBtn = document.getElementById("btn-start-camera");
    const captureBtn = document.getElementById("btn-capture-scan");
    const fileInput = document.getElementById("file-image-upload");
    const retakeBtn = document.getElementById("btn-retake");

    if (startCamBtn) {
        startCamBtn.addEventListener("click", startCamera);
    }

    if (captureBtn) {
        captureBtn.addEventListener("click", captureAndScan);
    }

    if (fileInput) {
        fileInput.addEventListener("change", handleFileUpload);
    }

    if (retakeBtn) {
        retakeBtn.addEventListener("click", resetCameraView);
    }
}

/**
 * Access device camera (prefers back camera if available on mobile)
 */
async function startCamera() {
    const video = document.getElementById("camera-video");
    const placeholder = document.getElementById("camera-placeholder");
    const startBtn = document.getElementById("btn-start-camera");
    const captureBtn = document.getElementById("btn-capture-scan");

    try {
        videoStream = await navigator.mediaDevices.getUserMedia({
            video: { facingMode: "environment", width: { ideal: 1280 }, height: { ideal: 720 } }
        });
        video.srcObject = videoStream;
        video.classList.remove("d-none");
        if (placeholder) placeholder.classList.add("d-none");
        if (startBtn) startBtn.classList.add("d-none");
        if (captureBtn) captureBtn.classList.remove("d-none");
        
        // Show scan laser line
        const laser = document.querySelector(".scan-laser");
        if (laser) laser.classList.remove("d-none");
    } catch (err) {
        console.error("Camera access error:", err);
        showToast("Unable to access camera directly. Please use the file upload option below.", "warning");
    }
}

/**
 * Capture frame from live video canvas and send to backend
 */
function captureAndScan() {
    const video = document.getElementById("camera-video");
    if (!video || !video.srcObject) {
        showToast("Please start the camera first.", "warning");
        return;
    }

    const canvas = document.createElement("canvas");
    canvas.width = video.videoWidth || 640;
    canvas.height = video.videoHeight || 480;
    const ctx = canvas.getContext("2d");
    ctx.drawImage(video, 0, 0, canvas.width, canvas.height);

    canvas.toBlob(blob => {
        const formData = new FormData();
        formData.append("image", blob, "captured_medicine.jpg");
        sendScanRequest(formData);
    }, "image/jpeg", 0.92);
}

/**
 * Handle direct file upload / drag-and-drop
 */
function handleFileUpload(e) {
    const file = e.target.files[0];
    if (!file) return;

    const formData = new FormData();
    formData.append("image", file, file.name);

    // Preview uploaded image
    const reader = new FileReader();
    reader.onload = (event) => {
        const preview = document.getElementById("camera-preview");
        const video = document.getElementById("camera-video");
        const placeholder = document.getElementById("camera-placeholder");
        if (preview) {
            preview.src = event.target.result;
            preview.classList.remove("d-none");
        }
        if (video) video.classList.add("d-none");
        if (placeholder) placeholder.classList.add("d-none");
    };
    reader.readAsDataURL(file);

    sendScanRequest(formData);
}

/**
 * Send image to `/api/camera/scan` and handle the result
 */
async function sendScanRequest(formData) {
    const loadingElem = document.getElementById("scan-loading");
    const resultContainer = document.getElementById("scan-result");
    const laser = document.querySelector(".scan-laser");

    if (loadingElem) loadingElem.classList.remove("d-none");
    if (resultContainer) resultContainer.classList.add("d-none");
    if (laser) laser.classList.remove("d-none");

    try {
        const res = await fetch("/api/camera/scan", {
            method: "POST",
            body: formData
        });
        const data = await res.json();

        if (loadingElem) loadingElem.classList.add("d-none");
        if (laser) laser.classList.add("d-none");
        if (resultContainer) resultContainer.classList.remove("d-none");

        if (data.status === "not_found" || !data.medicine_found) {
            // STRICT REQUIREMENT: Display exact string "Not a medicine found."
            displayScanNotFound(data.message || "Not a medicine found.");
        } else {
            displayScanSuccess(data);
        }
    } catch (err) {
        if (loadingElem) loadingElem.classList.add("d-none");
        if (laser) laser.classList.add("d-none");
        showToast("Error processing image. Please try again.", "danger");
    }
}

/**
 * Displays the strict "Not a medicine found." notification
 */
function displayScanNotFound(message) {
    const resultContainer = document.getElementById("scan-result");
    resultContainer.innerHTML = `
        <div class="alert alert-danger d-flex align-items-center p-4 rounded-4 shadow-sm" role="alert">
            <span class="fs-1 me-3">⚠️</span>
            <div>
                <h4 class="alert-heading fw-bold mb-1">Not a medicine found.</h4>
                <p class="mb-0 text-muted">The captured image does not contain a recognizable medicine package, label, or tablet. Please try repositioning the medicine label in good lighting, or enter it manually.</p>
            </div>
        </div>
        <div class="text-center mt-3">
            <button class="btn btn-outline-primary px-4 me-2" onclick="resetCameraView()">Try Again</button>
            <a href="/medicines/add" class="btn btn-primary px-4">Add Manually</a>
        </div>
    `;
}

/**
 * Displays successfully detected medicine and pre-filled form
 */
function displayScanSuccess(med) {
    const resultContainer = document.getElementById("scan-result");
    resultContainer.innerHTML = `
        <div class="card border-0 shadow-sm rounded-4 overflow-hidden">
            <div class="card-header bg-success text-white py-3 px-4 d-flex justify-content-between align-items-center">
                <span class="fw-bold fs-5">✓ Medicine Detected</span>
                <span class="badge bg-light text-success px-3 py-1 rounded-pill">OCR Verified</span>
            </div>
            <div class="card-body p-4">
                <div class="row g-3">
                    <div class="col-md-6">
                        <label class="form-label text-muted small fw-semibold">Medicine Name</label>
                        <h4 class="fw-bold text-dark mb-0">${med.name}</h4>
                        <small class="text-secondary">${med.generic_name || ""}</small>
                    </div>
                    <div class="col-md-6">
                        <label class="form-label text-muted small fw-semibold">Category</label>
                        <p class="fw-semibold text-primary mb-0">${med.category || "General"}</p>
                    </div>
                    <div class="col-md-4">
                        <label class="form-label text-muted small fw-semibold">Dosage</label>
                        <p class="fs-5 fw-bold mb-0 text-dark">${med.dosage_amount} ${med.dosage_unit}</p>
                    </div>
                    <div class="col-md-4">
                        <label class="form-label text-muted small fw-semibold">Daily Limit</label>
                        <p class="fw-semibold mb-0 text-secondary">${med.dosage_limit || "N/A"}</p>
                    </div>
                    <div class="col-md-4">
                        <label class="form-label text-muted small fw-semibold">Suggested Frequency</label>
                        <p class="fw-semibold mb-0 text-secondary">${med.frequency || "Daily"}</p>
                    </div>
                    <div class="col-12 mt-3">
                        <div class="p-3 bg-light rounded-3">
                            <label class="form-label text-muted small fw-bold mb-1">Clinical Instructions & Usage</label>
                            <p class="mb-0 text-dark small">${med.suggested_usage || med.notes || "Follow doctor prescription."}</p>
                        </div>
                    </div>
                </div>

                <hr class="my-4">

                <div class="d-flex justify-content-end gap-2">
                    <button class="btn btn-outline-secondary px-4" onclick="resetCameraView()">Scan Another</button>
                    <a href="/medicines/add?name=${encodeURIComponent(med.name)}&category=${encodeURIComponent(med.category || '')}&dosage=${encodeURIComponent(med.dosage_amount)}&unit=${encodeURIComponent(med.dosage_unit)}&freq=${encodeURIComponent(med.frequency || '')}&limit=${encodeURIComponent(med.dosage_limit || '')}&notes=${encodeURIComponent(med.notes || '')}" class="btn btn-primary px-4 fw-bold">
                        Continue & Save Schedule →
                    </a>
                </div>
            </div>
        </div>
    `;
}

function resetCameraView() {
    const resultContainer = document.getElementById("scan-result");
    const preview = document.getElementById("camera-preview");
    const video = document.getElementById("camera-video");
    const placeholder = document.getElementById("camera-placeholder");
    const startBtn = document.getElementById("btn-start-camera");
    const captureBtn = document.getElementById("btn-capture-scan");
    const fileInput = document.getElementById("file-image-upload");

    if (resultContainer) resultContainer.classList.add("d-none");
    if (preview) preview.classList.add("d-none");
    if (fileInput) fileInput.value = "";

    if (videoStream) {
        if (video) video.classList.remove("d-none");
        if (captureBtn) captureBtn.classList.remove("d-none");
    } else {
        if (placeholder) placeholder.classList.remove("d-none");
        if (startBtn) startBtn.classList.remove("d-none");
    }
}
