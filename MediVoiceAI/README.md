# MediVoice AI – Medicine Reminder and Voice Assistant

MediVoice AI is a full-stack Python and Flask web application built for healthcare medication compliance, automated dosage tracking, camera-based OCR label scanning, and interactive voice assistance.

---

## 🌟 Key Features

1. **User Authentication & OTP Security:**
   - Multi-factor sign in using either **Email Address** or **Phone Number**.
   - Secure OTP generation, validation, expiration, and resend workflows.
   - Protected routes and session management with password hashing.

2. **Real-Time Healthcare Dashboard:**
   - **Live 12-hour AM/PM clock** updating every second.
   - Comprehensive **Dosage Tracker** (Taken, Pending, Skipped, and Remaining doses).
   - Today's medication schedule with quick action triggers.

3. **Medicine Management:**
   - Add, edit, delete, and inspect medicine profiles (Dosage, Limits, Frequency, Times, Start/End Dates, Usage Notes).
   - Segregation of **Currently Active Medicines** and **Previously Used / Archived Medicines**.

4. **Medicine Reminder & Voice Notifications:**
   - Automatic schedule monitoring comparing current time with medicine reminders.
   - Audio chime alert accompanied by spoken voice announcement:
     > *“Reminder: It is time to take Paracetamol. Dosage: 500 mg.”*
   - Direct interactive modal to mark as **Taken**, **Skipped**, or **Pending**.

5. **Camera-Based Medicine Detection (OCR & AI):**
   - Live camera capture from phone/webcam or photo file upload.
   - Intelligent OCR reading of package labels, tablets, and bottles.
   - **Strict Verification:** If the image is non-medicine or unreadable, the system displays: **“Not a medicine found.”**
   - Automatically populates the medicine form for user review and confirmation.

6. **Interactive Python Voice Assistant:**
   - Hands-free voice recognition and speech synthesis.
   - Handles real-time queries against user database:
     - *“What medicines do I have today?”*
     - *“When is my next medicine reminder?”*
     - *“What is my dosage?”*
     - *“Add a medicine.”*
     - *“Show my medicine history.”*
     - *“What medicines are scheduled now?”*
     - *“Remind me about my medicine.”*

7. **AI Symptom & Clinical Guidance:**
   - Symptom-to-medicine educational guidance with mandatory clinical disclaimer.

8. **Dosage History & Audit:**
   - Complete searchable history filterable by status, date, and keyword.

---

## 🚀 Quick Start Guide (VS Code / Terminal)

### 1. Prerequisites
- Python 3.9+ installed
- Pip package manager

### 2. Installation
Open a terminal in the `MediVoiceAI` project folder:

```bash
cd MediVoiceAI

# (Optional) Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate    # On Windows use: venv\Scripts\activate

# Install required dependencies
pip install -r requirements.txt
```

### 3. Environment Setup
A sample `.env.example` is provided. Copy it to `.env`:

```bash
cp .env.example .env
```

### 4. Running the Application
Launch the Flask development server:

```bash
python app.py
```

The application will start on: **`http://localhost:5000`**

---

## 🔑 Default Demo Account
When first launched, MediVoice AI automatically seeds a sample patient account with initial active medications:

- **Email:** `patient@medivoice.ai`
- **Phone:** `+1234567890`
- **Password:** `password123`
- **OTP Code:** Upon sign in, the active 6-digit OTP code is displayed in the notification banner on the OTP page for immediate testing.

---

## 🧪 Testing Major Features

1. **Testing Sign In & OTP:**
   - Navigate to `http://localhost:5000/login`.
   - Enter `patient@medivoice.ai` and `password123`.
   - Enter the displayed 6-digit code on the OTP verification screen.

2. **Testing Live Clock & Audio Chime:**
   - On the Dashboard, verify the live clock seconds updating with AM/PM.
   - Click **"🔔 Test Voice Reminder"** on the dashboard to hear the chime and speech announcement.

3. **Testing Camera OCR:**
   - Click **"📷 Camera Scan"** in the top navigation.
   - Upload any medicine image containing a known medicine (e.g. Paracetamol, Amoxicillin, Ibuprofen).
   - Upload a random non-medicine image (e.g. a car, animal, or blank image) to see the mandatory warning: **“Not a medicine found.”**

4. **Testing Voice Assistant:**
   - Click **"🎙️ Voice Assistant"** in the menu.
   - Tap the microphone or click any of the sample command chips:
     - *“What medicines do I have today?”*
     - *“When is my next medicine reminder?”*
     - *“What is my dosage?”*
     - *“Show my medicine history.”*

5. **Testing Dosage Tracking:**
   - On the Dashboard today's schedule, click **"✓ Taken"** on any medicine.
   - Notice the "Taken Today" count increments and the "Remaining Doses" count updates instantly.
