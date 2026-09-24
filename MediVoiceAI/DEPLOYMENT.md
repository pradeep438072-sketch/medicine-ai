# MediVoice AI – Vercel Deployment Guide

This guide details the complete configuration and steps to deploy **MediVoice AI – Medicine Reminder and Voice Assistant** to [Vercel](https://vercel.com) with **zero 404 errors**.

---

## 1. Why 404 NOT_FOUND Occurred and How It Was Solved

Flask applications on Vercel run as Serverless WSGI functions. A `404 NOT_FOUND` error typically occurs due to:
1. **Missing Serverless Entry Point:** Vercel looks for functions in `api/`. Without `api/index.py` exporting the Flask WSGI instance (`app`), Vercel cannot invoke your application.
2. **Missing or Broken URL Rewrites:** Unlike a stateful VM running `python app.py`, Vercel routes incoming requests through an edge router. Without `vercel.json` rewrites, routes like `/dashboard`, `/login`, `/medicines`, and `/api/...` bypass the Flask app and return a 404 from Vercel's edge.
3. **Subdirectory vs Root Deployment:** If a repository has its application code in a subdirectory (e.g. `MediVoiceAI/`), deploying the repository root causes Vercel to look in the wrong directory.
4. **Read-Only Serverless Filesystem:** Local SQLite paths like `instance/medivoice.db` or uploads in `./uploads` crash on AWS Lambda / Vercel because the filesystem is read-only except for `/tmp`.

### Solutions Applied in This Project:
- Added `api/index.py` exporting `app` and `handler`.
- Added `vercel.json` with universal rewrites `[{"source": "/(.*)", "destination": "/api/index"}]`.
- Added support for **both** deployment workflows: deploying from the repo root or setting Root Directory to `MediVoiceAI`.
- Configured dynamic serverless fallback to `/tmp/medivoice.db` and `/tmp/uploads` to prevent read-only filesystem crashes.
- Added automatic PostgreSQL URL normalization (`postgres://` to `postgresql://`) for seamless compatibility with cloud databases (Neon, Supabase, Vercel Postgres).
- Added `psycopg2-binary` to `requirements.txt`.

---

## 2. Quick Deployment Steps on Vercel

### Step A: Push to GitHub / GitLab
Push your project files to your GitHub or GitLab repository.

### Step B: Import to Vercel
1. Go to your [Vercel Dashboard](https://vercel.com/dashboard) and click **"Add New..."** -> **"Project"**.
2. Select your repository.
3. In the project setup:
   - **Framework Preset:** `Other` (or leave default auto-detected)
   - **Root Directory:** You can leave it as default (`./`), or set it to `MediVoiceAI`. Both configurations are pre-configured and supported.

### Step C: Configure Environment Variables
Under the **Environment Variables** section in Vercel, add:

| Variable | Description | Example / Recommendation |
| :--- | :--- | :--- |
| `SECRET_KEY` | Flask session encryption key | Any strong random string (e.g., `prod-medivoice-secret-key-928472`) |
| `DATABASE_URL` | Persistent cloud PostgreSQL database | Neon / Supabase / Vercel Postgres connection string |
| `GEMINI_API_KEY` | (Optional) Gemini API key for OCR medicine packaging detection | Google AI Studio API Key |
| `FLASK_ENV` | Production environment flag | `production` |

> **Note on Database:** While the app gracefully falls back to an ephemeral SQLite database in `/tmp` for testing and preview builds, Vercel serverless functions are stateless. For persistent patient data across cold starts, link a free cloud PostgreSQL database (such as [Neon.tech](https://neon.tech), [Supabase](https://supabase.com), or Vercel Postgres) using `DATABASE_URL`.

### Step D: Click "Deploy"
Vercel will install dependencies from `requirements.txt`, build the serverless function, and provide you with a live production URL (e.g., `https://medivoice-ai.vercel.app`).

---

## 3. Verified Endpoints & Features

All routes are fully mapped and functional:
- **Authentication:** `/login`, `/register`, `/verify-otp`, `/resend-otp`, `/logout`
- **Dashboard & Live Clock:** `/dashboard` with 12-hour AM/PM real-time clock and dosage statistics
- **Medicine Management:** `/medicines`, `/medicines/add`, `/medicines/<id>`, `/medicines/<id>/edit`, `/medicines/<id>/delete`
- **Camera OCR & Scanning:** `/camera` and `/api/camera/scan`
- **Voice Assistant:** `/assistant` and `/api/voice/command`
- **AI Guidance & History:** `/suggestions` and `/history`
- **Reminder API:** `/api/reminders/today` and `/api/reminders/<id>/status`
