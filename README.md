# TASE Algorithmic Trading System

POC sentiment-based trading system for Tel Aviv Stock Exchange.

## Setup

1. Install dependencies:
   ```bash
   npm install
   pip install -r requirements.txt
   ```

2. Configure environment variables:
   ```bash
   cp .env.example .env
   # Fill in your API keys
   ```

3. Set up Supabase database:
   ```bash
   # Run schema.sql in Supabase SQL editor
   ```

4. Seed company mapping:
   ```bash
   python scripts/seed_company_mapping.py
   ```

5. Run locally:
   ```bash
   npm run dev
   ```

6. Deploy to Vercel:
   ```bash
   vercel deploy
   ```

## Architecture

See `docs/superpowers/specs/2026-03-30-tase-trading-system-design.md`

## Testing

```bash
npm test
```
