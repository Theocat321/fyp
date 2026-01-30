# Database Migrations

## Applying Migrations

### Via Supabase Dashboard (Recommended)

1. Go to your Supabase project dashboard
2. Navigate to SQL Editor
3. Copy the contents of the migration file
4. Paste and execute

### Via psql (Alternative)

```bash
psql "postgresql://[username]:[password]@[host]:5432/[database]?sslmode=require" \
  -f add_scenario_and_rubric_fields.sql
```

## Migration: add_scenario_and_rubric_fields.sql

**Date:** 2026-01-29
**Purpose:** Add scenario tracking and rubric ratings for human-LLM testing alignment

**Changes:**
- Add `scenario_id` to `participants` table
- Add `scenario_id` and rubric rating columns to `support_feedback` table
- Add indexes for query performance
