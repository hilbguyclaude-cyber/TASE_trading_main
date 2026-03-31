# TASE Algorithmic Trading System

🚀 **Production-ready** sentiment-based algorithmic trading system for Tel Aviv Stock Exchange.

## Features

✅ **Automated Sentiment Analysis** - AI-powered (Gemini 1.5 Flash) analysis of TASE announcements
✅ **Position Management** - Automatic buy/sell with 60-minute hold OR -1% stop-loss
✅ **Visual Dashboard** - Real-time Next.js dashboard with positions and announcements
✅ **Email Alerts** - Trade notifications via Resend API
✅ **System Health Monitoring** - Auto-pause trading when services are unhealthy
✅ **90 Passing Tests** - Comprehensive test suite with TDD methodology

## Quick Start

### Option 1: Automated Deployment (Recommended)

```bash
./deploy.sh
```

The interactive wizard will:
1. Check prerequisites (Node.js, npm, Vercel CLI)
2. Guide you through API key setup
3. Deploy to Vercel with environment variables
4. Provide next steps

### Option 2: Manual Deployment

See **[DEPLOYMENT.md](DEPLOYMENT.md)** for comprehensive step-by-step instructions.

## Dashboard Preview

Once deployed, you'll have access to:

- **📊 Dashboard** (`/`) - System status, statistics, recent activity
- **📈 Positions** (`/positions`) - Open and closed positions with P/L tracking
- **📰 Announcements** (`/announcements`) - Sentiment-analyzed TASE announcements

## Architecture

```
Next.js Dashboard (3 pages) → Vercel Serverless Functions (4 endpoints)
                              ↓
Supabase (PostgreSQL) ← → External APIs:
  - 6 tables                  - Gemini 1.5 Flash (sentiment)
  - Real-time logs            - Yahoo Finance (prices)
  - Position tracking         - TASE RSS/API (announcements)
                              - Resend (email alerts)
```

## Trading Logic

**Buy Trigger:**
- POSITIVE sentiment with ≥70% confidence
- Position size: MIN(1% of daily volume, ₪5,000)
- Only during TASE trading hours

**Sell Trigger (whichever comes first):**
- Hold for 60 minutes, OR
- Price drops -1% from peak price

## Project Status

| Component | Status | Tests |
|-----------|--------|-------|
| Database Schema | ✅ Complete | - |
| Database Utilities | ✅ Complete | 7 passing |
| Gemini Client | ✅ Complete | 10 passing |
| Yahoo Finance Client | ✅ Complete | 16 passing |
| TASE Scraper | ✅ Complete | 17 passing |
| Trading Logic | ✅ Complete | 21 passing |
| System Health | ✅ Complete | 23 passing |
| API: Check Announcements | ✅ Complete | 7 passing |
| API: Analyze Sentiment | ✅ Complete | 7 passing |
| API: Monitor Positions | ✅ Complete | 9 passing |
| API: Send Email | ✅ Complete | 7 passing |
| Dashboard Pages | ✅ Complete | - |
| **Total** | **100%** | **90 passing** |

## Development

### Local Testing

```bash
# Install dependencies
npm install
pip install -r requirements.txt

# Run tests
pytest tests/ -v

# Run development server
npm run dev
```

### Environment Variables

Required for deployment:
- `SUPABASE_URL` - Database URL
- `SUPABASE_SERVICE_KEY` - Database service role key
- `GEMINI_API_KEY` - Google AI Studio API key
- `RESEND_API_KEY` - Email API key
- `ALERT_EMAIL_FROM` - Sender email (verified in Resend)
- `ALERT_EMAIL_TO` - Your email for alerts

See [DEPLOYMENT.md](DEPLOYMENT.md) for detailed setup instructions.

## File Structure

```
.
├── api/                      # Vercel serverless functions
│   ├── cron/
│   │   ├── check_announcements.py    # Fetch TASE announcements
│   │   └── monitor_positions.py      # Monitor & close positions
│   ├── analyze_sentiment.py          # Gemini sentiment analysis
│   └── send_email.py                 # Resend email notifications
├── app/                      # Next.js 14 App Router
│   ├── layout.tsx            # Root layout with navigation
│   ├── page.tsx              # Dashboard home
│   ├── positions/page.tsx    # Positions tracking
│   ├── announcements/page.tsx # Announcements feed
│   └── lib/supabase.ts       # Database client & types
├── lib/                      # Python business logic
│   ├── db.py                 # Database utilities
│   ├── gemini_client.py      # AI sentiment analysis
│   ├── yfinance_client.py    # Price fetching
│   ├── tase_scraper.py       # Announcement scraping
│   ├── trading_logic.py      # Buy/sell decisions
│   └── system_health.py      # Health monitoring
├── tests/                    # Comprehensive test suite (90 tests)
├── schema.sql                # Database schema
├── vercel.json               # Cron job configuration
├── DEPLOYMENT.md             # Deployment guide
└── deploy.sh                 # Automated deployment script
```

## Cron Jobs

Two cron jobs run every 1 minute:

1. **check_announcements** - Fetches TASE announcements, maps to tickers
2. **monitor_positions** - Updates peak prices, closes positions on exit criteria

**Note**: Vercel cron requires Pro plan ($20/month). Free tier can use external cron services like cron-job.org.

## Cost Estimate

- **Vercel Pro**: $20/month (includes cron jobs)
- **Supabase**: Free tier (500MB database)
- **Gemini 1.5 Flash**: Free tier (15 RPM, 1500 RPD)
- **Resend**: Free tier (100 emails/day)
- **Yahoo Finance**: Free (rate-limited)

**Total**: ~$20/month for production deployment

## Documentation

- **[DEPLOYMENT.md](DEPLOYMENT.md)** - Complete deployment guide
- **[schema.sql](schema.sql)** - Database schema with comments
- **System Design** - See `docs/superpowers/specs/`

## Support

- **Issues**: Report bugs at [GitHub Issues](https://github.com/hilbguyclaude-cyber/TASE_trading_main/issues)
- **Logs**: `vercel logs --follow` or Vercel Dashboard
- **Database Logs**: Supabase Dashboard → Logs

## Safety & Disclaimer

⚠️ **This is a proof-of-concept system for educational purposes.**

- Always test thoroughly with paper trading before live deployment
- Monitor system health and position limits
- Set appropriate risk management parameters
- Past sentiment performance does not predict future results

## License

MIT License - See LICENSE file for details

---

Built with ❤️ using Claude Code (TDD methodology, 90 passing tests)
