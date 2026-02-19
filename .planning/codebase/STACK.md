# Technology Stack

**Analysis Date:** 2026-02-19

## Languages

**Primary:**
- TypeScript 5.9.3 - Used in Next.js frontend (`/Users/stagcto/fyp/web/app`) and API routes
- Python 3.9+ - Used in FastAPI backend (`/Users/stagcto/fyp/server/app` and `/Users/stagcto/fyp/server/api`)

**Secondary:**
- JavaScript/JSX - Next.js configuration and React components

## Runtime

**Environment:**
- Node.js >=18 (specified in `web/package.json`)
- Python 3.9+ with venv (`/Users/stagcto/fyp/server/venv`)

**Package Managers:**
- npm - Node.js dependencies in `web/`
- pip - Python dependencies in `server/` and `llm-testing/`
- Lockfile: `web/package-lock.json` present

## Frameworks

**Core:**
- Next.js 14.2.15 - Full-stack React framework with API routes
- FastAPI 0.115.0 - Async Python web framework for backend endpoints
- React 18.3.1 - UI library for `web/` frontend
- React DOM 18.3.1 - React DOM bindings

**Build/Dev:**
- TypeScript 5.9.3 - Type checking for Next.js and API code
- Node.js module bundler (Next.js built-in)

## Key Dependencies

**Critical:**
- @supabase/supabase-js 2.46.1 - Supabase client for Next.js API routes and feedback storage
- openai 4.63.0 - OpenAI API client (JavaScript version in `web/`, Python version in `server/`)
- uvicorn[standard] 0.30.6 - ASGI server for FastAPI in production

**Infrastructure:**
- pydantic 2.9.2 - Data validation for FastAPI request/response models
- python-dotenv >=1.0.1 - Environment variable loading in both Node and Python
- requests >=2.32.0 - HTTP client for Supabase REST calls in Python backend
- PyYAML >=6.0.1 - YAML parsing for LLM testing framework

**Type Support:**
- @types/node 24.6.2 - Node.js type definitions
- @types/react 19.2.0 - React type definitions
- @types/phoenix (installed via dependencies) - WebSocket type definitions

## Configuration

**Environment:**
- Unified `.env` file in repository root (`/Users/stagcto/fyp/.env`)
- Separate `.env.example` documents required configuration
- Environment variables shared between Next.js and FastAPI:
  - `OPENAI_API_KEY` - OpenAI authentication
  - `OPENAI_MODEL` - Model selection (default: gpt-4o-mini)
  - `OPENAI_BASE_URL` - Optional custom OpenAI endpoint
  - `SUPABASE_URL` - Supabase project URL
  - `SUPABASE_SERVICE_ROLE_KEY` - Supabase service role key
  - `PROVIDER_NAME` - Brand name (default: VodaCare)
  - `ASSISTANT_MODE` - "open" or "strict" mode
  - `ALLOWED_ORIGINS` - CORS origins for FastAPI (default: http://localhost:3000)

**Frontend-specific (NEXT_PUBLIC_*):**
- `NEXT_PUBLIC_API_BASE_URL` - Optional backend proxy URL
- `NEXT_PUBLIC_SUPABASE_URL` - Supabase URL for browser
- `NEXT_PUBLIC_SUPABASE_ANON_KEY` - Supabase anon key for browser
- `NEXT_PUBLIC_USE_STREAMING` - Enable streaming UX (default: true)

**Build:**
- `tsconfig.json` in `/Users/stagcto/fyp/web/` - TypeScript compilation target ES2020, strict mode enabled
- `next.config.mjs` in `/Users/stagcto/fyp/web/` - Handles rewrites for local API proxying, loads root .env
- `vercel.json` - Deployment configuration for Vercel with Next.js build and Python serverless functions

## Platform Requirements

**Development:**
- macOS/Linux/Windows with Node.js >=18 and Python 3.9+
- npm and pip package managers
- Supabase project (optional for backend storage)
- OpenAI API key (optional for LLM features)

**Production:**
- Vercel deployment platform (configured in `vercel.json`)
- Can also run standalone with Python FastAPI backend on any server
- PostgreSQL backend required if using Supabase

---

*Stack analysis: 2026-02-19*
