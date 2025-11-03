# Step-by-Step Server Restart Guide

## ✅ Memory Fix Verification

The memory collection fix has been applied:
- **File**: `tradingagents/agents/utils/memory.py`
- **Line 15**: Uses `get_or_create_collection` instead of `create_collection`
- **Status**: ✅ Fix is in place

This fix handles all memory collections:
- `bull_memory`
- `bear_memory` 
- `trader_memory`
- `invest_judge_memory`
- `risk_manager_memory`

## 🔄 Step-by-Step Restart Instructions

### Step 1: Find and Stop Current Server

**Option A: Using Process ID**
```bash
# Find the server process
lsof -ti:8000

# Kill the process (replace PID with actual number)
kill -9 <PID>
```

**Option B: Find the Terminal**
- Look for the terminal window running `python server.py` or `uvicorn`
- Press `Ctrl+C` to stop it gracefully

### Step 2: Verify Server Stopped

```bash
# Check if port 8000 is free
lsof -i:8000

# Should show: No process found (or empty output)
```

### Step 3: Start Server Again

```bash
# Start the server
python server.py
```

Or if using uvicorn directly:
```bash
uvicorn tradingagents.api.server:app --host 0.0.0.0 --port 8000
```

### Step 4: Verify Server Started Successfully

Wait for these messages:
```
Starting TradingAgents API server on 0.0.0.0:8000
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8000
```

### Step 5: Test the Server

```bash
# Test health endpoint
curl http://localhost:8000/api/v1/health
```

Expected response:
```json
{
  "status": "ok",
  "version": "1.0.0",
  "timestamp": "..."
}
```

### Step 6: Test Memory Collections

The `bull_memory` collection error should no longer occur when:
- Running analysis via API
- Using the Report tab in frontend
- Initializing TradingAgentsGraph

## 🔍 Troubleshooting

### If port is still in use:
```bash
# Find what's using port 8000
lsof -i:8000

# Kill it
kill -9 <PID>

# Or use alternative port
TRADINGAGENTS_PORT=8001 python server.py
```

### If memory error still occurs:
1. Check ChromaDB collections exist:
   ```python
   import chromadb
   client = chromadb.Client()
   collections = client.list_collections()
   print([c.name for c in collections])
   ```

2. Delete old collections if needed:
   ```python
   client.delete_collection("bull_memory")
   # Server will recreate on next run
   ```

## ✅ Success Indicators

After restart, you should see:
- ✅ Server starts without errors
- ✅ No "collection already exists" errors
- ✅ API health check responds
- ✅ Report tab works without backend errors

## 📝 Quick Reference

```bash
# One-line restart (if you know the PID)
kill -9 $(lsof -ti:8000) && python server.py

# Or just stop and restart manually
# 1. Find terminal with server
# 2. Press Ctrl+C
# 3. Run: python server.py
```

