#!/bin/bash
# TASE Trading System - Quick Deploy Script
# This script helps you deploy the system step-by-step

set -e  # Exit on error

echo "🚀 TASE Trading System - Deployment Wizard"
echo "==========================================="
echo ""

# Color codes
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Check prerequisites
echo "📋 Checking prerequisites..."
echo ""

# Check Node.js
if ! command -v node &> /dev/null; then
    echo -e "${RED}❌ Node.js not found${NC}"
    echo "   Install from: https://nodejs.org/"
    echo "   Or via Homebrew: brew install node"
    exit 1
else
    NODE_VERSION=$(node --version)
    echo -e "${GREEN}✅ Node.js installed${NC} ($NODE_VERSION)"
fi

# Check npm
if ! command -v npm &> /dev/null; then
    echo -e "${RED}❌ npm not found${NC}"
    exit 1
else
    NPM_VERSION=$(npm --version)
    echo -e "${GREEN}✅ npm installed${NC} ($NPM_VERSION)"
fi

# Check/Install Vercel CLI
if ! command -v vercel &> /dev/null; then
    echo -e "${YELLOW}⚠️  Vercel CLI not found${NC}"
    echo "   Installing Vercel CLI globally..."
    npm install -g vercel
    echo -e "${GREEN}✅ Vercel CLI installed${NC}"
else
    VERCEL_VERSION=$(vercel --version)
    echo -e "${GREEN}✅ Vercel CLI installed${NC} ($VERCEL_VERSION)"
fi

echo ""
echo "🔑 API Keys Required"
echo "===================="
echo ""
echo "Before deploying, you need to collect these API keys:"
echo ""
echo "1. Supabase (Database)"
echo "   • Go to: https://supabase.com/dashboard"
echo "   • Create project → Get URL and service_role key"
echo ""
echo "2. Gemini API (Sentiment Analysis)"
echo "   • Go to: https://aistudio.google.com/app/apikey"
echo "   • Create API key"
echo ""
echo "3. Resend API (Email Notifications)"
echo "   • Go to: https://resend.com/api-keys"
echo "   • Create API key (free tier: 100 emails/day)"
echo ""

# Prompt to continue
read -p "Have you collected all API keys? (y/n): " -n 1 -r
echo ""
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo -e "${YELLOW}⏸️  Please collect API keys first, then run this script again.${NC}"
    echo ""
    echo "📖 See DEPLOYMENT.md for detailed instructions."
    exit 0
fi

echo ""
echo "📝 Environment Configuration"
echo "============================="
echo ""

# Collect environment variables
read -p "Enter SUPABASE_URL: " SUPABASE_URL
read -p "Enter SUPABASE_SERVICE_KEY: " SUPABASE_SERVICE_KEY
read -p "Enter GEMINI_API_KEY: " GEMINI_API_KEY
read -p "Enter RESEND_API_KEY: " RESEND_API_KEY
read -p "Enter ALERT_EMAIL_FROM (e.g., alerts@yourdomain.com): " ALERT_EMAIL_FROM
read -p "Enter ALERT_EMAIL_TO (your email): " ALERT_EMAIL_TO

# Create .env.local for testing
cat > .env.local <<EOF
# Database
SUPABASE_URL=$SUPABASE_URL
SUPABASE_SERVICE_KEY=$SUPABASE_SERVICE_KEY

# AI & APIs
GEMINI_API_KEY=$GEMINI_API_KEY
RESEND_API_KEY=$RESEND_API_KEY

# Email Configuration
ALERT_EMAIL_FROM=$ALERT_EMAIL_FROM
ALERT_EMAIL_TO=$ALERT_EMAIL_TO

# Timezone
TZ=Asia/Jerusalem
EOF

echo -e "${GREEN}✅ Environment variables saved to .env.local${NC}"
echo ""

# Login to Vercel
echo "🔐 Logging into Vercel..."
vercel login

echo ""
echo "🚀 Deploying to Vercel..."
echo "========================="
echo ""

# Deploy to production
vercel --prod \
  -e SUPABASE_URL="$SUPABASE_URL" \
  -e SUPABASE_SERVICE_KEY="$SUPABASE_SERVICE_KEY" \
  -e GEMINI_API_KEY="$GEMINI_API_KEY" \
  -e RESEND_API_KEY="$RESEND_API_KEY" \
  -e ALERT_EMAIL_FROM="$ALERT_EMAIL_FROM" \
  -e ALERT_EMAIL_TO="$ALERT_EMAIL_TO" \
  -e TZ="Asia/Jerusalem"

echo ""
echo -e "${GREEN}✅ Deployment complete!${NC}"
echo ""
echo "📊 Next Steps:"
echo "=============="
echo ""
echo "1. Open your Vercel dashboard to get your deployment URL"
echo "2. Visit https://your-app.vercel.app to see your dashboard"
echo "3. Enable cron jobs in Vercel dashboard (requires Pro plan)"
echo "   • Settings → Cron Jobs → Enable both cron jobs"
echo ""
echo "4. Test the deployment:"
echo "   curl https://your-app.vercel.app/api/health"
echo ""
echo "5. Initialize database in Supabase:"
echo "   • Go to Supabase → SQL Editor"
echo "   • Run the schema.sql file"
echo "   • Run: INSERT INTO system_status ..."
echo ""
echo "📖 See DEPLOYMENT.md for detailed post-deployment steps."
echo ""
echo -e "${GREEN}🎉 Your TASE Trading System is live!${NC}"
