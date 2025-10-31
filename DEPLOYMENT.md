# Deployment Guide for TradingAgents API Server

This guide covers deploying the TradingAgents FastAPI server to various cloud platforms with free tiers.

## Table of Contents

- [Quick Summary](#quick-summary)
- [Platform Comparison](#platform-comparison)
- [Recommended: Render](#recommended-render)
- [Alternative: Railway](#alternative-railway)
- [Alternative: Fly.io](#alternative-flyio)
- [Environment Variables](#environment-variables)
- [Post-Deployment](#post-deployment)

---

## Quick Summary

**Best Free Options (2025):**

1. **Render** ⭐ **Recommended** - 750 hours/month, easiest setup, auto-deploy from GitHub
2. **Railway** - 500 hours/month, $5 credit monthly, great UX
3. **Fly.io** - Generous free tier, global edge deployment
4. **PythonAnywhere** - Free tier for testing, limited for production

**For Production:**
- Start with Render (easiest)
- Consider Railway for $5/month paid (more reliable)
- Fly.io for global distribution

---

## Platform Comparison

| Platform | Free Tier | Pros | Cons | Best For |
|----------|-----------|------|------|----------|
| **Render** | 750 hrs/month | Auto-deploy, easiest setup, GitHub integration | Sleeps after 15min inactivity | Development, demos |
| **Railway** | 500 hrs + $5 credit | Great UX, Docker support, excellent docs | Limited free tier | Small production apps |
| **Fly.io** | Generous limits | Global edge, no sleep, fast deploys | More complex setup | Production apps |
| **PythonAnywhere** | Free tier | Simple Python hosting | Slow free tier, limited features | Testing only |
| **Heroku** | Discontinued | N/A | No free tier anymore | N/A |
| **Vercel** | Generous | Great for Next.js frontends | Not ideal for FastAPI | Frontend hosting |

---

## Recommended: Render

**Why Render:** Best balance of ease, reliability, and free tier.

### Setup Steps

1. **Create Render Account**
   - Go to https://render.com
   - Sign up with GitHub

2. **Create New Web Service**
   - Click "New +" → "Web Service"
   - Connect your GitHub repo: `TradingAgents`
   - Select branch: `feature/data-vendor-integration`

3. **Configure Service**
   ```
   Name: tradingagents-api
   Region: Oregon (or closest to you)
   Branch: feature/data-vendor-integration
   Root Directory: (leave empty)
   
   Build Command:
   pip install -r requirements.txt
   
   Start Command:
   uvicorn tradingagents.api.server:app --host 0.0.0.0 --port $PORT
   ```

4. **Add Environment Variables**
   ```
   OPENAI_API_KEY=your_openai_key
   ALPHA_VANTAGE_API_KEY=your_alphavantage_key
   TUSHARE_API_KEY=your_tushare_key
   FINNHUB_API_KEY=your_finnhub_key
   ANTHROPIC_API_KEY=your_anthropic_key (optional)
   GOOGLE_API_KEY=your_google_key (optional)
   TRADINGAGENTS_DEBUG=false
   ```

5. **Deploy**
   - Click "Create Web Service"
   - Render will build and deploy automatically
   - Your API will be live at: `https://tradingagents-api.onrender.com`

### Pros
- ✅ Auto-deploy on git push
- ✅ Free SSL certificate
- ✅ Easy rollback
- ✅ Logs dashboard
- ✅ No credit card required

### Cons
- ❌ Free tier sleeps after 15 min inactivity (first request wakes it)
- ❌ Build timeout: 45 min
- ❌ Memory: 512 MB RAM

### Tips
- Add `/health` endpoint to any monitoring service to prevent sleep
- Use `--reload` only in dev (not in production)
- Set `TRADINGAGENTS_DEBUG=false` for production

---

## Alternative: Railway

**Why Railway:** Great developer experience with $5 monthly credit.

### Setup Steps

1. **Create Railway Account**
   - Go to https://railway.app
   - Sign up with GitHub

2. **Create New Project**
   - Click "New Project"
   - Select "Deploy from GitHub repo"
   - Choose `TradingAgents` repo

3. **Configure Deployment**
   - Railway auto-detects Python
   - It will create a `railway.toml` if needed

4. **Create `railway.toml`** (optional, for customization)
   ```toml
   [build]
   builder = "NIXPACKS"

   [deploy]
   startCommand = "uvicorn tradingagents.api.server:app --host 0.0.0.0 --port $PORT"
   restartPolicyType = "ON_FAILURE"
   restartPolicyMaxRetries = 10
   ```

5. **Add Environment Variables**
   - Go to "Variables" tab
   - Add all your API keys (same as Render)

6. **Generate Domain**
   - Go to "Settings" → "Networking"
   - Click "Generate Domain"
   - Your API: `https://tradingagents-production.up.railway.app`

### Pros
- ✅ $5 monthly credit included
- ✅ Great Docker support
- ✅ No cold starts (if within credit)
- ✅ Excellent logs and metrics
- ✅ Easy database integration

### Cons
- ❌ Free credits expire monthly
- ❌ May cost money after credit used
- ❌ Less generous than Render free tier

---

## Alternative: Fly.io

**Why Fly.io:** Global edge deployment, very generous free tier, no sleep.

### Setup Steps

1. **Install Fly CLI**
   ```bash
   curl -L https://fly.io/install.sh | sh
   ```

2. **Login to Fly**
   ```bash
   fly auth login
   ```

3. **Initialize Fly App**
   ```bash
   cd TradingAgents
   fly launch
   ```
   
   Answer prompts:
   - App name: `tradingagents-api` (or your choice)
   - Region: `sjc` (San Jose, or closest to you)
   - Database: No
   - Redis: No (unless you need it)

4. **Create `fly.toml`**
   ```toml
   app = "tradingagents-api"
   primary_region = "sjc"

   [build]
     builder = "paketobuildpacks/builder:base"

   [env]
     PORT = "8080"
     TRADINGAGENTS_HOST = "0.0.0.0"

   [[services]]
     internal_port = 8080
     processes = ["app"]
     protocol = "tcp"
     script_checks = []
     
     [services.concurrency]
       type = "connections"
       hard_limit = 25
       soft_limit = 20

     [[services.ports]]
       handlers = ["http"]
       port = 80

     [[services.ports]]
       handlers = ["tls", "http"]
       port = 443

     [[services.http_checks]]
       interval = "10s"
       timeout = "5s"
       grace_period = "30s"
       method = "GET"
       path = "/api/v1/health"
   ```

5. **Update Start Command in `fly.toml`**
   ```toml
   [env]
     PORT = "8080"
   ```
   
   Add to `Dockerfile` or create one:
   ```dockerfile
   FROM python:3.11-slim
   
   WORKDIR /app
   COPY requirements.txt .
   RUN pip install --no-cache-dir -r requirements.txt
   
   COPY . .
   
   CMD ["uvicorn", "tradingagents.api.server:app", "--host", "0.0.0.0", "--port", "8080"]
   ```

6. **Set Secrets**
   ```bash
   fly secrets set OPENAI_API_KEY=your_key
   fly secrets set ALPHA_VANTAGE_API_KEY=your_key
   # ... add all other keys
   ```

7. **Deploy**
   ```bash
   fly deploy
   ```

### Pros
- ✅ No cold starts (always running)
- ✅ Global edge locations
- ✅ Very generous free tier
- ✅ Fast deploys
- ✅ Great for production

### Cons
- ❌ CLI required (less GUI-friendly)
- ❌ More complex setup
- ❌ Requires Docker knowledge

---

## Environment Variables

**Required for all platforms:**

```bash
# OpenAI (required for MCP integration)
OPENAI_API_KEY=sk-...

# Alpha Vantage (required for market data)
ALPHA_VANTAGE_API_KEY=...

# Tushare (optional, for A-shares data)
TUSHARE_API_KEY=...

# Finnhub (optional, for news/sentiment)
FINNHUB_API_KEY=...

# Anthropic (optional, for Claude models)
ANTHROPIC_API_KEY=sk-ant-...

# Google (optional, for Gemini models)
GOOGLE_API_KEY=...

# Server Configuration
TRADINGAGENTS_HOST=0.0.0.0
TRADINGAGENTS_PORT=8000
TRADINGAGENTS_DEBUG=false
```

**Security Tips:**
- Never commit API keys to git
- Use platform's environment variable UI
- Rotate keys regularly
- Use separate keys for prod/dev

---

## Post-Deployment

### 1. Test Your Deployment

```bash
# Health check
curl https://your-app.onrender.com/api/v1/health

# Run analysis (example)
curl -X POST https://your-app.onrender.com/api/v1/analyze \
  -H "Content-Type: application/json" \
  -d '{"ticker": "TSLA", "date": "2024-10-31"}'
```

### 2. Monitor Logs

**Render:**
- Dashboard → Your Service → Logs

**Railway:**
- Dashboard → Your Service → Deployments → Logs

**Fly.io:**
```bash
fly logs
```

### 3. Set Up Auto-Deploy

All platforms support auto-deploy on git push. Just:
1. Connect GitHub repo
2. Enable auto-deploy
3. Push to your branch
4. Platform deploys automatically

### 4. Add Custom Domain (Optional)

**Render:**
- Settings → Custom Domain → Add your domain

**Railway:**
- Settings → Networking → Add custom domain

**Fly.io:**
```bash
fly domains add yourdomain.com
```

### 5. Configure CORS (if needed)

Update `tradingagents/api/server.py`:
```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://your-frontend.com",
        "https://localhost:3000",  # local dev
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)
```

---

## Performance Tips

### Optimize for Free Tier

1. **Reduce Cold Starts**
   - Use health checks to keep service awake
   - Use Railway $5 credit for no-sleep tier
   - Or use Fly.io (no sleep)

2. **Reduce Memory Usage**
   - Set `TRADINGAGENTS_DEBUG=false`
   - Disable unnecessary logging
   - Use connection pooling for databases

3. **Optimize Startup**
   - Lazy-load heavy dependencies
   - Cache initialization data
   - Use async operations

4. **Scale Smartly**
   - Start with Render free tier
   - Move to Railway paid if traffic grows
   - Use Fly.io for global distribution

---

## Troubleshooting

### "Build failed" on Render/Railway

```bash
# Check build logs
# Common issues:
- Python version mismatch (add runtime.txt: python-3.11.0)
- Missing dependencies (check requirements.txt)
- Build timeout (reduce dependencies)
```

### "Application crashed" on start

```bash
# Check application logs
# Common issues:
- Missing environment variables
- Port binding error (use $PORT env var)
- Import errors (check Python path)
```

### "Cold start too slow"

```bash
# Solutions:
- Switch to Railway paid or Fly.io
- Optimize startup code
- Pre-warm with health checks
```

---

## Cost Comparison

| Platform | Free Tier | Paid Cost (after free) | Recommended For |
|----------|-----------|-------------------------|-----------------|
| Render | 750 hrs/month | $7/month (Starter) | Testing, demos |
| Railway | 500 hrs + $5 | Pay-as-you-go | Small production |
| Fly.io | Generous | ~$5-20/month | Production |
| VPS (DigitalOcean) | $0 | $6/month (min) | Self-hosted |

**Recommendation:**
- Start: Render (free)
- Growth: Railway ($7-15/month)
- Scale: Fly.io or VPS

---

## Next Steps

1. Deploy to Render for testing
2. Test all endpoints
3. Set up monitoring
4. Configure custom domain (optional)
5. Scale to Railway/Fly.io if needed

**Questions?** Check platform docs or open an issue in the repo.

