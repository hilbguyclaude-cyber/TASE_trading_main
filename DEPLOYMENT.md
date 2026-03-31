# TASE Trading System - Deployment Guide

Complete guide to deploy your sentiment-based algorithmic trading system to production.

## Prerequisites

Before deploying, ensure you have:

- ✅ Supabase account (free tier works)
- ✅ Vercel account (free tier works)
- ✅ Gemini API key (from Google AI Studio)
- ✅ Resend API key (for email notifications)
- ✅ Vercel CLI installed: `npm i -g vercel`

## Step 1: Database Setup (Supabase)

### 1.1 Create Supabase Project

1. Go to https://supabase.com/dashboard
2. Click "New Project"
3. Choose organization and name: `tase-trading`
4. Generate a strong database password
5. Select region closest to you
6. Wait for provisioning (~2 minutes)

### 1.2 Run Database Schema

1. In Supabase dashboard, go to **SQL Editor**
2. Click "New Query"
3. Copy the entire contents of `schema.sql` from this repo
4. Paste and click "Run"
5. Verify 6 tables created: `system_status`, `system_logs`, `companies`, `announcements`, `positions`, `unmapped_companies`

### 1.3 Get Database Credentials

1. Go to **Project Settings** → **API**
2. Copy the following values:
   - **URL**: `https://xxxxx.supabase.co`
   - **anon key**: `eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...` (public, safe to expose)
   - **service_role key**: `eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...` (secret, never commit!)

### 1.4 Initialize System Status

Run this SQL query in Supabase SQL Editor:

```sql
INSERT INTO system_status (status, buying_enabled, selling_enabled, metadata)
VALUES ('HEALTHY', true, true, '{"initialized": true, "version": "1.0.0"}')
ON CONFLICT (id) DO NOTHING;
```

## Step 2: Get API Keys

### 2.1 Gemini API Key

1. Go to https://aistudio.google.com/app/apikey
2. Click "Create API Key"
3. Choose "Create API key in new project" or select existing project
4. Copy the API key: `AIzaSy...`

### 2.2 Resend API Key

1. Go to https://resend.com/api-keys
2. Sign up if needed (free tier: 100 emails/day)
3. Click "Create API Key"
4. Name it: `TASE Trading Alerts`
5. Copy the key: `re_...`

## Step 3: Vercel Deployment

### 3.1 Install Vercel CLI (if not already installed)

```bash
npm install -g vercel
```

### 3.2 Login to Vercel

```bash
vercel login
```

Follow the prompts to authenticate.

### 3.3 Deploy from Worktree

```bash
cd /Users/guy.hilb/TASE_trading_main/.worktrees/implementation
vercel --prod
```

### 3.4 Configure Environment Variables

During deployment, Vercel will prompt for environment variables. Set these:

```bash
# Database
SUPABASE_URL=https://xxxxx.supabase.co
SUPABASE_SERVICE_KEY=eyJhbGci...  # service_role key from Step 1.3

# AI & APIs
GEMINI_API_KEY=AIzaSy...  # from Step 2.1
RESEND_API_KEY=re_...  # from Step 2.2

# Email Configuration
ALERT_EMAIL_FROM=alerts@yourdomain.com  # Must be verified in Resend
ALERT_EMAIL_TO=your-email@example.com  # Your email for trade alerts

# Optional: Set timezone (defaults to Asia/Jerusalem)
TZ=Asia/Jerusalem
```

**Alternative: Set via Vercel Dashboard**

If you prefer, set environment variables via Vercel dashboard:
1. Go to your project in Vercel dashboard
2. Navigate to **Settings** → **Environment Variables**
3. Add each variable above
4. Redeploy: `vercel --prod`

## Step 4: Enable Cron Jobs

Vercel cron jobs are defined in `vercel.json` but need to be enabled:

### 4.1 Verify Cron Configuration

Check `vercel.json` contains:

```json
{
  "crons": [
    {
      "path": "/api/cron/check_announcements",
      "schedule": "* * * * *"
    },
    {
      "path": "/api/cron/monitor_positions",
      "schedule": "* * * * *"
    }
  ]
}
```

### 4.2 Enable Cron Jobs in Vercel

1. Go to your project in Vercel dashboard
2. Navigate to **Settings** → **Cron Jobs**
3. You should see 2 cron jobs:
   - `check_announcements` - Runs every 1 minute
   - `monitor_positions` - Runs every 1 minute
4. Ensure both are **Enabled**

**Note**: Cron jobs only work on Vercel's **Pro plan** ($20/month). On the free Hobby plan, cron jobs won't execute. You can:
- Upgrade to Pro for production use
- Use external cron services (e.g., cron-job.org) to hit your endpoints
- Manually trigger endpoints for testing

### 4.3 Manual Cron Testing (Free Tier Alternative)

If you want to test without upgrading:

```bash
# Check announcements manually
curl -X POST https://your-app.vercel.app/api/cron/check_announcements

# Monitor positions manually
curl -X POST https://your-app.vercel.app/api/cron/monitor_positions
```

## Step 5: Verify Deployment

### 5.1 Check Dashboard

1. Open your Vercel deployment URL: `https://your-app.vercel.app`
2. You should see the **Dashboard** with:
   - System Status card (should show "HEALTHY")
   - Statistics (will be empty initially)
   - Recent Announcements (empty until first scrape)
   - Recent Positions (empty until first trade)

### 5.2 Verify API Endpoints

Test each endpoint manually:

```bash
# 1. Health check
curl https://your-app.vercel.app/api/health

# 2. Fetch announcements (triggers scraper)
curl -X POST https://your-app.vercel.app/api/cron/check_announcements

# 3. Analyze sentiment (processes pending announcements)
curl -X POST https://your-app.vercel.app/api/analyze_sentiment

# 4. Monitor positions (checks exit conditions)
curl -X POST https://your-app.vercel.app/api/cron/monitor_positions
```

### 5.3 Check Supabase Data

1. Go to Supabase dashboard → **Table Editor**
2. Check `system_logs` table - should see API calls logged
3. Check `announcements` table - should populate after first scrape
4. Check `system_status` table - should show "HEALTHY"

### 5.4 Test Email Notifications

Create a test position manually in Supabase to trigger a sell email:

```sql
-- Insert a test position (will trigger sell on next monitor cycle)
INSERT INTO positions (ticker, entry_price, peak_price, position_size_ils, entry_time, sentiment, confidence)
VALUES ('TASE', 100.0, 100.0, 1000.0, NOW() - INTERVAL '2 hours', 'POSITIVE', 0.85);
```

Wait 1 minute for the monitor cron to run, then check your email.

## Step 6: Monitoring & Maintenance

### 6.1 Monitor Logs

View real-time logs in Vercel:
```bash
vercel logs --follow
```

Or in Vercel Dashboard:
1. Go to your project
2. Navigate to **Deployments** → Select latest deployment
3. Click **Functions** tab to see serverless function logs

### 6.2 Monitor Database

Check Supabase logs:
1. Go to Supabase dashboard
2. Navigate to **Logs** → **Database**
3. Monitor queries and errors

### 6.3 System Health Dashboard

Use the built-in system health page:
- Dashboard shows system status (HEALTHY/DEGRADED/DOWN)
- Check `/api/health` endpoint for detailed health report
- System auto-pauses buying if critical services fail

### 6.4 Email Alerts

You'll receive email notifications for:
- **BUY alerts**: When POSITIVE sentiment triggers new position
- **SELL alerts**: When position exits (with P/L details)

### 6.5 Manual Overrides

Pause/resume trading via Supabase SQL Editor:

```sql
-- Pause all trading
UPDATE system_status
SET buying_enabled = false, selling_enabled = false
WHERE id = 1;

-- Resume trading
UPDATE system_status
SET buying_enabled = true, selling_enabled = true
WHERE id = 1;

-- Pause only buying (let existing positions close)
UPDATE system_status
SET buying_enabled = false
WHERE id = 1;
```

## Troubleshooting

### Issue: "Missing environment variables"

**Solution**: Ensure all required env vars are set in Vercel dashboard:
```bash
vercel env pull  # Download current env vars
vercel env add SUPABASE_URL  # Add missing var
vercel --prod  # Redeploy
```

### Issue: "Supabase connection failed"

**Solution**:
1. Verify `SUPABASE_URL` and `SUPABASE_SERVICE_KEY` are correct
2. Check Supabase project is running (not paused)
3. Ensure service_role key is used (not anon key)

### Issue: "Gemini API quota exceeded"

**Solution**:
1. Check quota in Google AI Studio
2. Upgrade to paid tier if needed
3. Reduce `max_announcements` in `analyze_sentiment.py`

### Issue: "Cron jobs not running"

**Solution**:
1. Upgrade to Vercel Pro plan ($20/month) for cron support
2. Or use external cron service: https://cron-job.org
   - Set URL: `https://your-app.vercel.app/api/cron/check_announcements`
   - Schedule: Every 1 minute

### Issue: "Email notifications not working"

**Solution**:
1. Verify Resend API key is valid
2. Ensure `ALERT_EMAIL_FROM` is verified in Resend dashboard
3. Check Resend logs: https://resend.com/logs
4. Test manually: `curl -X POST https://your-app.vercel.app/api/send_email`

### Issue: "Announcements not showing"

**Solution**:
1. Manually trigger scraper: `curl -X POST https://your-app.vercel.app/api/cron/check_announcements`
2. Check `system_logs` table for scraper errors
3. TASE RSS feed may be down - system will auto-fallback to API

### Issue: "Positions not closing"

**Solution**:
1. Check `monitor_positions` cron is running
2. Verify `selling_enabled = true` in `system_status` table
3. Manually trigger: `curl -X POST https://your-app.vercel.app/api/cron/monitor_positions`
4. Check position exit conditions (60min OR -1% from peak)

## Production Checklist

Before going live with real trading:

- [ ] All environment variables set in Vercel
- [ ] Supabase database schema applied
- [ ] System status initialized
- [ ] Cron jobs enabled (or external cron configured)
- [ ] Email notifications tested
- [ ] Dashboard accessible and showing data
- [ ] Health check passing: `curl https://your-app.vercel.app/api/health`
- [ ] Test announcement → sentiment → position flow manually
- [ ] Verify sell logic with mock position
- [ ] Set appropriate `buying_enabled` flag based on your risk tolerance

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                         Vercel (Hosting)                         │
├─────────────────────────────────────────────────────────────────┤
│  Next.js Dashboard (app/)                                       │
│  ├── / (Dashboard)                 [60s revalidation]           │
│  ├── /positions                    [30s revalidation]           │
│  └── /announcements                [30s revalidation]           │
├─────────────────────────────────────────────────────────────────┤
│  Serverless Functions (api/)                                    │
│  ├── /api/cron/check_announcements    [Cron: every 1 min]     │
│  ├── /api/cron/monitor_positions      [Cron: every 1 min]     │
│  ├── /api/analyze_sentiment           [HTTP trigger]           │
│  └── /api/send_email                  [HTTP trigger]           │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│                      External Services                           │
├─────────────────────────────────────────────────────────────────┤
│  Supabase (Database)          [PostgreSQL]                      │
│  Gemini 1.5 Flash            [Sentiment Analysis]               │
│  Yahoo Finance API           [Stock Prices]                     │
│  TASE RSS/API                [Announcements]                    │
│  Resend                      [Email Notifications]              │
└─────────────────────────────────────────────────────────────────┘
```

## Data Flow

1. **Every 1 minute** (Cron):
   - `check_announcements` fetches TASE announcements → stores in DB
   - `monitor_positions` checks open positions → closes if exit criteria met

2. **Sentiment Analysis** (Triggered manually or by webhook):
   - Fetches unanalyzed announcements
   - Sends to Gemini for sentiment analysis
   - If POSITIVE + buying_enabled → creates position
   - Sends BUY email notification

3. **Position Lifecycle**:
   ```
   Announcement → Sentiment Analysis → BUY Decision
        ↓
   Open Position (entry_price, entry_time)
        ↓
   Monitor (update peak_price every minute)
        ↓
   Exit Check (60min OR -1% from peak) → SELL Decision
        ↓
   Closed Position (P/L calculated) → SELL email sent
   ```

## Cost Estimate (Free Tier)

- **Vercel Hobby**: Free (no cron support)
- **Vercel Pro**: $20/month (includes cron jobs)
- **Supabase**: Free up to 500MB database
- **Gemini 1.5 Flash**: Free tier (15 RPM, 1M TPM, 1500 RPD)
- **Resend**: Free tier (100 emails/day, 1 domain)
- **Yahoo Finance API**: Free (rate-limited)

**Recommended for production**: Vercel Pro + Free tiers = ~$20/month

## Next Steps

1. ✅ Deploy to Vercel
2. ✅ Verify dashboard loads
3. ✅ Test announcement scraping
4. ✅ Test sentiment analysis
5. ✅ Monitor first position lifecycle
6. ⏳ Paper trade for 1 week to validate logic
7. ⏳ Connect real brokerage API (future enhancement)

---

**🎉 You now have a production-ready algorithmic trading system!**

Questions? Check the logs first:
- Vercel logs: `vercel logs --follow`
- Supabase logs: Dashboard → Logs
- System logs: Query `system_logs` table
