# Quick Deploy to Render (5 Minutes)

Fastest way to get your TradingAgents API live.

## Prerequisites

- GitHub repo pushed to remote
- Render account (free): https://render.com
- API keys ready

---

## Step-by-Step

### 1. Create Render Account (1 min)

Go to https://render.com → Sign up with GitHub

### 2. Create Web Service (2 min)

1. Click "New +" → "Web Service"
2. Connect GitHub repo: `TradingAgents`
3. Click "Connect"

### 3. Configure Service (1 min)

**Settings:**
```
Name: tradingagents-api
Region: Oregon (or closest to you)
Branch: feature/data-vendor-integration (or main)
```

**Build & Deploy:**
```
Build Command:
pip install -r requirements.txt

Start Command:
uvicorn tradingagents.api.server:app --host 0.0.0.0 --port $PORT
```

### 4. Add Environment Variables (1 min)

Click "Advanced" → "Add Environment Variable"

Add these:
```
OPENAI_API_KEY=sk-...
ALPHA_VANTAGE_API_KEY=...
TUSHARE_API_KEY=...
FINNHUB_API_KEY=...
TRADINGAGENTS_DEBUG=false
```

(Optional: Add ANTHROPIC_API_KEY, GOOGLE_API_KEY if using)

### 5. Deploy! (2 min)

Click "Create Web Service"

Render will:
1. Build your app
2. Install dependencies
3. Deploy to production

Wait ~2-3 minutes for first build.

---

## Your API is Live!

**URL:** `https://tradingagents-api.onrender.com`

**Test it:**
```bash
curl https://tradingagents-api.onrender.com/api/v1/health
```

**API Docs:**
https://tradingagents-api.onrender.com/docs

---

## Auto-Deploy Setup

**Enabled by default!**

Every git push to `feature/data-vendor-integration` will:
1. Trigger new deployment
2. Build latest code
3. Restart service

No manual deploy needed! 🎉

---

## Keep Service Awake (Optional)

Free tier sleeps after 15 min inactivity.

**Option 1: Cron Job** (recommended)
```bash
# Run every 10 minutes
*/10 * * * * curl https://tradingagents-api.onrender.com/api/v1/health
```

**Option 2: UptimeRobot** (free)
1. Sign up: https://uptimerobot.com
2. Add monitor: `https://tradingagents-api.onrender.com/api/v1/health`
3. Interval: 5 minutes

**Option 3: Wake by First Request**
Just wait 30-60 seconds on first request after sleep.

---

## Custom Domain (Optional)

1. Settings → "Custom Domain"
2. Enter your domain: `api.yourdomain.com`
3. Add CNAME record in DNS:
   ```
   api.yourdomain.com → tradingagents-api.onrender.com
   ```
4. Render auto-generates SSL certificate

---

## Logs & Monitoring

**View Logs:**
Dashboard → Your Service → "Logs" tab

**View Metrics:**
Dashboard → Your Service → "Metrics" tab

---

## Troubleshooting

### Build Failed

**Check logs for errors:**
- Python version (add `runtime.txt`: `python-3.11.0`)
- Missing dependencies
- Import errors

**Solution:**
```bash
# Add runtime.txt in root
python-3.11.0
```

### Service Won't Start

**Check start command:**
```
uvicorn tradingagents.api.server:app --host 0.0.0.0 --port $PORT
```

**Common issues:**
- Wrong host (use `0.0.0.0`)
- Wrong port (use `$PORT`, not hardcoded)
- Missing env vars

### Cold Start Too Slow

**Free tier limitation:** First request after sleep takes 30-60s

**Solutions:**
1. Use UptimeRobot to prevent sleep
2. Upgrade to Starter plan ($7/month)
3. Use Railway or Fly.io instead

---

## Security Checklist

- ✅ Environment variables set in Render (not in code)
- ✅ No API keys in GitHub
- ✅ TRADINGAGENTS_DEBUG=false for production
- ✅ CORS configured (update allow_origins)
- ✅ Custom domain with SSL (if using)

---

## Next Steps

1. ✅ Deploy to Render
2. ✅ Test endpoints
3. ✅ Configure monitoring
4. 📖 Read full guide: [DEPLOYMENT.md](DEPLOYMENT.md)

**Questions?** Check Render docs: https://render.com/docs

