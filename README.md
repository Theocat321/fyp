# VodaCare Support Chatbot (Next.js + FastAPI)

A local full‑stack customer support chatbot specialized for a mobile network provider (think Vodafone). Frontend is Next.js, backend is FastAPI. No production setup — local dev only.

## Quick Start

- Prerequisites: Node.js 18+, Python 3.10+
- Ports: frontend `3000`, backend `8000`

1) Copy env files

- Root example: `.env.example`
- Recommended copies:
  - `cp server/.env.example server/.env`
  - `cp web/.env.example web/.env.local`

2) Backend (FastAPI)

- From `server/`:
  - Create venv and install: `python -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt`
  - Run API: `uvicorn app.main:app --reload --port 8000`

3) Frontend (Next.js)

- From `web/`:
  - Install deps: `npm install`
  - Run dev server: `npm run dev`
  - Open: `http://localhost:3000`

## Features

- Mobile telco–themed chatbot with friendly tone
- Common intents: plans, upgrades, data/balance, roaming, billing, coverage, support
- Suggestions (quick replies) returned by API and shown as chips
- Simple rule-based agent (no external API needed)

## Configuration

- Frontend reads `NEXT_PUBLIC_API_BASE_URL` to call the backend
- Backend reads `ALLOWED_ORIGINS` for theming/CORS

## Project Structure

- `server/` FastAPI app and chatbot logic
- `web/` Next.js app with chat UI

## Notes

- All data is in-memory; restarting the API clears session history.
- This is a local dev setup; no production configs included.
