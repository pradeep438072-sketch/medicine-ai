# MediVoice AI – Vercel Deployment Guide

This project is fully configured for deployment on [Vercel](https://vercel.com) with **zero 404 errors**.

### Supported Deployment Modes
You can deploy this project in either of two ways:
1. **Repository Root Deployment (Default):** Leave Root Directory as `./` on Vercel. Root `api/index.py` and `vercel.json` will route all traffic directly to MediVoice AI.
2. **Subdirectory Deployment:** Set **Root Directory** in Vercel project settings to `MediVoiceAI`. `MediVoiceAI/api/index.py` and `MediVoiceAI/vercel.json` will handle the build.

### Environment Variables on Vercel
- `SECRET_KEY`: Long random string for session signing.
- `DATABASE_URL`: Cloud PostgreSQL URL (e.g., from Neon.tech, Supabase, or Vercel Postgres).
- `GEMINI_API_KEY`: (Optional) AI Vision & OCR assistance key from Google AI Studio.
- `FLASK_ENV`: `production`

Refer to `MediVoiceAI/DEPLOYMENT.md` for full documentation.
