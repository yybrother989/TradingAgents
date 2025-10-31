# Quick Start - TradingAgents API Server

## ✅ Server Status Check

Your local server is **ready to connect**! Here's a quick verification:

### Prerequisites Check

Run this to verify your setup:

```bash
python -c "
from tradingagents.api.server import app
print('✅ Server ready!')
print(f'Available at: http://localhost:8000')
print(f'API Docs: http://localhost:8000/docs')
"
```

## 🚀 Starting the Server

### Option 1: Using the server.py script (Recommended)

```bash
python server.py
```

### Option 2: Using uvicorn directly

```bash
uvicorn tradingagents.api.server:app --host 0.0.0.0 --port 8000 --reload
```

### Option 3: Using python -m

```bash
python -m uvicorn tradingagents.api.server:app --host 0.0.0.0 --port 8000
```

## 🔍 Verify Server is Running

Once started, you should see:

```
Starting TradingAgents API server on 0.0.0.0:8000
Debug mode: False
API docs available at: http://0.0.0.0:8000/docs
INFO:     Started server process
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8000
```

### Test the Server

**1. Health Check:**
```bash
curl http://localhost:8000/api/v1/health
```

Expected response:
```json
{
  "status": "ok",
  "version": "1.0.0",
  "timestamp": "2024-05-10T12:00:00"
}
```

**2. Check API Documentation:**
Open in browser: `http://localhost:8000/docs`

**3. Test Analysis Endpoint:**
```bash
curl -X POST "http://localhost:8000/api/v1/analyze" \
  -H "Content-Type: application/json" \
  -d '{"ticker": "AAPL", "date": "2024-05-10"}'
```

## ⚙️ Configuration

### Environment Variables (Optional)

Create a `.env` file in the project root:

```bash
# Server Configuration
TRADINGAGENTS_HOST=0.0.0.0
TRADINGAGENTS_PORT=8000
TRADINGAGENTS_DEBUG=false

# API Keys (Required for full functionality)
OPENAI_API_KEY=your_openai_api_key_here
ALPHA_VANTAGE_API_KEY=your_alpha_vantage_api_key_here
```

### Default Configuration

- **Host**: `0.0.0.0` (accessible from all network interfaces)
- **Port**: `8000`
- **Debug**: `false`
- **CORS**: Enabled for all origins (development)

## 🌐 Access Points

Once the server is running, you can access:

- **API Base URL**: `http://localhost:8000`
- **API Documentation (Swagger)**: `http://localhost:8000/docs`
- **API Documentation (ReDoc)**: `http://localhost:8000/redoc`
- **Health Check**: `http://localhost:8000/api/v1/health`
- **Root Endpoint**: `http://localhost:8000/`

## 📡 Frontend Connection

### Quick Test from Browser Console

Open browser console (F12) and run:

```javascript
// Test health endpoint
fetch('http://localhost:8000/api/v1/health')
  .then(r => r.json())
  .then(data => console.log('✅ Server is running:', data));

// Test analysis (requires API keys)
fetch('http://localhost:8000/api/v1/analyze', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ ticker: 'AAPL', date: '2024-05-10' })
})
  .then(r => r.json())
  .then(data => console.log('✅ Analysis result:', data))
  .catch(err => console.error('❌ Error:', err));
```

### CORS Configuration

The server has CORS enabled by default:
- **Development**: Allows all origins (`*`)
- **Production**: Update `tradingagents/api/server.py` to restrict origins

## 🔧 Troubleshooting

### Port Already in Use

If port 8000 is already in use:

```bash
# Option 1: Use a different port
TRADINGAGENTS_PORT=8001 python server.py

# Option 2: Find and kill the process using port 8000
# macOS/Linux:
lsof -ti:8000 | xargs kill -9
```

### Import Errors

If you see import errors:

```bash
# Verify dependencies are installed
pip install -r requirements.txt

# Or if using uv
uv sync
```

### MCP Connection Issues

If MCP initialization fails, the server will still start but analyst agents may not work fully. Check logs for MCP-related warnings.

## ✅ Server Readiness Checklist

- [x] FastAPI installed
- [x] Uvicorn installed
- [x] Server module imports successfully
- [x] All routes configured
- [x] CORS middleware enabled
- [ ] Server started (run `python server.py`)
- [ ] Health endpoint responding (test with curl)
- [ ] API docs accessible (visit `/docs`)

## 📚 Next Steps

1. **Start the server**: `python server.py`
2. **Verify it's running**: Visit `http://localhost:8000/docs`
3. **Connect your frontend**: See [FRONTEND_INTEGRATION.md](FRONTEND_INTEGRATION.md)
4. **Test an analysis**: Use the `/api/v1/analyze` endpoint

## 🎯 Quick Test Script

Save this as `test_server.py`:

```python
#!/usr/bin/env python3
"""Quick test script to verify server is ready."""

import requests
import sys

BASE_URL = "http://localhost:8000"

def test_health():
    """Test health endpoint."""
    try:
        response = requests.get(f"{BASE_URL}/api/v1/health", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Health check passed: {data['status']}")
            return True
        else:
            print(f"❌ Health check failed: {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print(f"❌ Cannot connect to {BASE_URL}")
        print("   Make sure the server is running: python server.py")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def test_docs():
    """Test if docs are accessible."""
    try:
        response = requests.get(f"{BASE_URL}/docs", timeout=5)
        if response.status_code == 200:
            print("✅ API documentation is accessible")
            return True
        else:
            print(f"⚠️  Docs returned status {response.status_code}")
            return False
    except Exception as e:
        print(f"⚠️  Could not access docs: {e}")
        return False

if __name__ == "__main__":
    print("Testing TradingAgents API Server...")
    print("=" * 50)
    
    health_ok = test_health()
    docs_ok = test_docs()
    
    print("=" * 50)
    if health_ok:
        print("✅ Server is ready and responding!")
        print(f"📚 API Docs: {BASE_URL}/docs")
        print(f"🔍 Health: {BASE_URL}/api/v1/health")
    else:
        print("❌ Server is not ready")
        print("   Start the server with: python server.py")
        sys.exit(1)
```

Run it with:
```bash
python test_server.py
```

