# Frontend Integration Guide - TradingAgents Analyst API

This guide explains how to connect your frontend application to the TradingAgents Analyst API. The API provides access to analyst reports including Market Analysis, News Analysis, Social Media Sentiment Analysis, and Fundamentals Analysis.

## Table of Contents

- [Quick Start](#quick-start)
- [API Overview](#api-overview)
- [Base Configuration](#base-configuration)
- [API Endpoints](#api-endpoints)
- [Type Definitions](#type-definitions)
- [Frontend Examples](#frontend-examples)
  - [React with TypeScript](#react-with-typescript)
  - [Vue 3 with TypeScript](#vue-3-with-typescript)
  - [Vanilla JavaScript](#vanilla-javascript)
  - [Next.js](#nextjs)
- [Error Handling](#error-handling)
- [CORS Configuration](#cors-configuration)
- [Best Practices](#best-practices)
- [Complete Example](#complete-example)

## Quick Start

1. **Start the API server** (if running locally):
   ```bash
   python server.py
   # Or
   uvicorn tradingagents.api.server:app --host 0.0.0.0 --port 8000
   ```

2. **Set the base URL** in your frontend:
   ```typescript
   const API_BASE_URL = 'http://localhost:8000';
   // Or production: 'https://api.yourdomain.com'
   ```

3. **Make your first request**:
   ```javascript
   const response = await fetch(`${API_BASE_URL}/api/v1/analyze`, {
     method: 'POST',
     headers: { 'Content-Type': 'application/json' },
     body: JSON.stringify({
       ticker: 'AAPL',
       date: '2024-05-10'
     })
   });
   const data = await response.json();
   ```

## API Overview

The TradingAgents Analyst API exposes **only analyst outputs**:
- ✅ Market/Technical Analysis
- ✅ News Analysis
- ✅ Social Media/Sentiment Analysis
- ✅ Fundamentals Analysis
- ❌ Trading decisions (excluded)
- ❌ Researcher outputs (excluded)
- ❌ Risk manager outputs (excluded)

## Base Configuration

### API Base URL

```typescript
// Development
const API_BASE_URL = 'http://localhost:8000';

// Production (update with your actual domain)
const API_BASE_URL = 'https://api.yourdomain.com';
```

### Common Headers

All API requests should include:

```typescript
const headers = {
  'Content-Type': 'application/json',
  'Accept': 'application/json'
};

// If authentication is required (future)
const headersWithAuth = {
  ...headers,
  'Authorization': `Bearer ${yourToken}`
};
```

## API Endpoints

### 1. Run Analyst Agents

**Endpoint:** `POST /api/v1/analyze`

Runs all analyst agents and returns their reports for a given ticker and date.

**Request:**
```typescript
interface AnalyzeRequest {
  ticker: string;      // e.g., "AAPL", "NVDA"
  date: string;        // YYYY-MM-DD format, e.g., "2024-05-10"
  config?: {           // Optional configuration override
    [key: string]: any;
  };
}
```

**Response:**
```typescript
interface AnalyzeResponse {
  ticker: string;
  date: string;
  reports: {
    market_report?: {
      content: string;
      timestamp?: string;
    };
    sentiment_report?: {
      content: string;
      timestamp?: string;
    };
    news_report?: {
      content: string;
      timestamp?: string;
    };
    fundamentals_report?: {
      content: string;
      timestamp?: string;
    };
  };
  execution_time: number;  // in seconds
  timestamp: string;        // ISO 8601 format
}
```

**Example:**
```typescript
const response = await fetch(`${API_BASE_URL}/api/v1/analyze`, {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    ticker: 'AAPL',
    date: '2024-05-10'
  })
});

const data: AnalyzeResponse = await response.json();
console.log(data.reports.market_report?.content);
```

---

### 2. Run Selected Analyst Agents

**Endpoint:** `POST /api/v1/agents/run`

Run specific analyst agents independently.

**Request:**
```typescript
interface RunAgentsRequest {
  ticker: string;
  date: string;
  agents?: string[];  // Optional: ["market_analyst", "news_analyst", "social_analyst", "fundamentals_analyst"]
  config?: {
    [key: string]: any;
  };
}
```

**Response:**
```typescript
interface RunAgentsResponse {
  ticker: string;
  date: string;
  agents: string[];  // List of agents that were executed
  results: {
    [agentName: string]: {
      report: string;
      success: boolean;
      execution_time: number;
      error?: string;
    };
  };
}
```

**Valid Agent Names:**
- `market_analyst` - Market/Technical analysis
- `news_analyst` - News and macroeconomic analysis
- `social_analyst` - Social media sentiment analysis
- `fundamentals_analyst` - Company fundamentals analysis

**Example:**
```typescript
const response = await fetch(`${API_BASE_URL}/api/v1/agents/run`, {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    ticker: 'AAPL',
    date: '2024-05-10',
    agents: ['market_analyst', 'news_analyst']  // Only run these two
  })
});

const data: RunAgentsResponse = await response.json();
```

---

### 3. Get Cached Analysis

**Endpoint:** `GET /api/v1/analyses/{ticker}/{date}`

Retrieve cached analyst reports if available.

**Example:**
```typescript
const response = await fetch(`${API_BASE_URL}/api/v1/analyses/AAPL/2024-05-10`);
const data = await response.json();
```

---

### 4. Stream Analysis (Real-time Progressive Updates)

**Endpoint:** `GET /api/v1/analyze/stream`

**Perfect for daily report generation!** Stream analysis results in real-time as each analyst completes. Frontend receives updates progressively, no need to wait for all reports.

**Parameters:**
- `ticker`: Stock ticker symbol (query parameter)
- `date`: Trading date in YYYY-MM-DD format (query parameter)
- `config`: Optional JSON-encoded configuration override (query parameter)

**Event Types:**
- `start`: Analysis started
- `report`: Individual report completed (contains report data)
- `complete`: All reports finished
- `error`: Error occurred

**Example (JavaScript EventSource):**
```javascript
const eventSource = new EventSource(
  `/api/v1/analyze/stream?ticker=TSLA&date=2024-10-31`
);

eventSource.addEventListener('start', (e) => {
  const data = JSON.parse(e.data);
  console.log(`Analysis started for ${data.ticker}`);
});

eventSource.addEventListener('report', (e) => {
  const data = JSON.parse(e.data);
  console.log(`${data.agent} completed:`, data.report);
  // Update UI with this report immediately
  updateReportInUI(data.report_key, data.report);
  
  // Show progress
  console.log(`Progress: ${data.progress.percentage}% (${data.progress.completed}/${data.progress.total})`);
});

eventSource.addEventListener('complete', (e) => {
  const data = JSON.parse(e.data);
  console.log('All reports complete:', data.reports);
  console.log(`Total execution time: ${data.execution_time}s`);
  eventSource.close();
});

eventSource.addEventListener('error', (e) => {
  const data = JSON.parse(e.data);
  console.error('Error:', data.error);
  eventSource.close();
});
```

**React Hook Example:**
```typescript
// hooks/useStreamingAnalysis.ts
import { useState, useEffect, useCallback } from 'react';

const API_BASE_URL = process.env.REACT_APP_API_BASE_URL || 'http://localhost:8000';

export function useStreamingAnalysis() {
  const [reports, setReports] = useState<Record<string, any>>({});
  const [progress, setProgress] = useState({ completed: 0, total: 0, percentage: 0 });
  const [status, setStatus] = useState<'idle' | 'streaming' | 'complete' | 'error'>('idle');
  const [error, setError] = useState<string | null>(null);

  const startStreaming = useCallback((ticker: string, date: string) => {
    setStatus('streaming');
    setReports({});
    setProgress({ completed: 0, total: 0, percentage: 0 });
    setError(null);

    const eventSource = new EventSource(
      `${API_BASE_URL}/api/v1/analyze/stream?ticker=${ticker}&date=${date}`
    );

    eventSource.addEventListener('start', (e) => {
      const data = JSON.parse(e.data);
      setProgress({ completed: 0, total: data.total_agents, percentage: 0 });
    });

    eventSource.addEventListener('report', (e) => {
      const data = JSON.parse(e.data);
      setReports(prev => ({
        ...prev,
        [data.report_key]: data.report
      }));
      setProgress(data.progress);
    });

    eventSource.addEventListener('complete', (e) => {
      const data = JSON.parse(e.data);
      setReports(data.reports);
      setStatus('complete');
      eventSource.close();
    });

    eventSource.addEventListener('error', (e) => {
      const data = JSON.parse(e.data);
      setError(data.error);
      setStatus('error');
      eventSource.close();
    });

    eventSource.onerror = () => {
      setError('Connection error');
      setStatus('error');
      eventSource.close();
    };

    return () => {
      eventSource.close();
    };
  }, []);

  return { reports, progress, status, error, startStreaming };
}

// Usage in component
function DailyReportGenerator() {
  const { reports, progress, status, error, startStreaming } = useStreamingAnalysis();

  const handleGenerate = () => {
    startStreaming('TSLA', '2024-10-31');
  };

  return (
    <div>
      <button onClick={handleGenerate} disabled={status === 'streaming'}>
        Generate Daily Report
      </button>

      {status === 'streaming' && (
        <div>
          <progress value={progress.percentage} max={100} />
          <p>{progress.completed} / {progress.total} reports completed</p>
        </div>
      )}

      {reports.market_report && (
        <section>
          <h3>Market Analysis ✅</h3>
          <div>{reports.market_report.content}</div>
        </section>
      )}

      {reports.news_report && (
        <section>
          <h3>News Analysis ✅</h3>
          <div>{reports.news_report.content}</div>
        </section>
      )}

      {/* More reports... */}
    </div>
  );
}
```

**Benefits for Daily Report Generation:**
- ✅ **Progressive Updates**: Frontend receives reports as they complete
- ✅ **No Waiting**: Users see results immediately, not after all agents finish
- ✅ **Better UX**: Real-time progress bars and status updates
- ✅ **Efficient**: Agents run in parallel, reports stream as completed
- ✅ **Cache-Friendly**: Cached results returned immediately if available

---

### 5. Health Check

**Endpoint:** `GET /api/v1/health`

Check if the API server is running.

**Response:**
```typescript
interface HealthResponse {
  status: string;      // "ok"
  version: string;    // API version
  timestamp: string;
}
```

**Example:**
```typescript
const response = await fetch(`${API_BASE_URL}/api/v1/health`);
const data: HealthResponse = await response.json();
if (data.status === 'ok') {
  console.log('API is healthy');
}
```

---

### 6. Get Configuration

**Endpoint:** `GET /api/v1/config`

Get current API configuration.

---

### 7. Update Configuration

**Endpoint:** `POST /api/v1/config`

Update API configuration (typically for admin use).

---

## Type Definitions

### TypeScript Definitions

Save this as `tradingagents-api.d.ts` in your project:

```typescript
// tradingagents-api.d.ts

export interface ReportSection {
  content: string;
  timestamp?: string;
}

export interface AnalysisReports {
  market_report?: ReportSection;
  sentiment_report?: ReportSection;
  news_report?: ReportSection;
  fundamentals_report?: ReportSection;
}

export interface AnalyzeRequest {
  ticker: string;
  date: string;
  config?: Record<string, any>;
}

export interface AnalyzeResponse {
  ticker: string;
  date: string;
  reports: AnalysisReports;
  execution_time: number;
  timestamp: string;
}

export interface RunAgentsRequest {
  ticker: string;
  date: string;
  agents?: ('market_analyst' | 'news_analyst' | 'social_analyst' | 'fundamentals_analyst')[];
  config?: Record<string, any>;
}

export interface AgentResult {
  report: string;
  success: boolean;
  execution_time: number;
  error?: string;
}

export interface RunAgentsResponse {
  ticker: string;
  date: string;
  agents: string[];
  results: Record<string, AgentResult>;
}

export interface HealthResponse {
  status: string;
  version: string;
  timestamp: string;
}

export interface ApiError {
  error: string;
  detail?: string;
  timestamp: string;
}
```

## Frontend Examples

### React with TypeScript

#### API Service Hook

```typescript
// hooks/useTradingAgentsApi.ts
import { useState, useCallback } from 'react';

const API_BASE_URL = process.env.REACT_APP_API_BASE_URL || 'http://localhost:8000';

export function useTradingAgentsApi() {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const analyzeStock = useCallback(async (ticker: string, date: string) => {
    setLoading(true);
    setError(null);
    
    try {
      const response = await fetch(`${API_BASE_URL}/api/v1/analyze`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ ticker, date }),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Analysis failed');
      }

      const data: AnalyzeResponse = await response.json();
      return data;
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Unknown error';
      setError(message);
      throw err;
    } finally {
      setLoading(false);
    }
  }, []);

  const runAgents = useCallback(async (
    ticker: string,
    date: string,
    agents?: string[]
  ) => {
    setLoading(true);
    setError(null);
    
    try {
      const response = await fetch(`${API_BASE_URL}/api/v1/agents/run`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ ticker, date, agents }),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Agent execution failed');
      }

      const data: RunAgentsResponse = await response.json();
      return data;
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Unknown error';
      setError(message);
      throw err;
    } finally {
      setLoading(false);
    }
  }, []);

  const checkHealth = useCallback(async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/api/v1/health`);
      const data: HealthResponse = await response.json();
      return data.status === 'ok';
    } catch {
      return false;
    }
  }, []);

  return {
    analyzeStock,
    runAgents,
    checkHealth,
    loading,
    error,
  };
}
```

#### Component Example

```typescript
// components/StockAnalysis.tsx
import React, { useState } from 'react';
import { useTradingAgentsApi } from '../hooks/useTradingAgentsApi';
import type { AnalyzeResponse } from '../types/tradingagents-api';

export function StockAnalysis() {
  const [ticker, setTicker] = useState('AAPL');
  const [date, setDate] = useState(new Date().toISOString().split('T')[0]);
  const [analysis, setAnalysis] = useState<AnalyzeResponse | null>(null);
  const { analyzeStock, loading, error } = useTradingAgentsApi();

  const handleAnalyze = async () => {
    try {
      const result = await analyzeStock(ticker, date);
      setAnalysis(result);
    } catch (err) {
      console.error('Analysis failed:', err);
    }
  };

  return (
    <div className="stock-analysis">
      <div className="controls">
        <input
          type="text"
          value={ticker}
          onChange={(e) => setTicker(e.target.value.toUpperCase())}
          placeholder="Ticker (e.g., AAPL)"
        />
        <input
          type="date"
          value={date}
          onChange={(e) => setDate(e.target.value)}
        />
        <button onClick={handleAnalyze} disabled={loading}>
          {loading ? 'Analyzing...' : 'Analyze'}
        </button>
      </div>

      {error && <div className="error">Error: {error}</div>}

      {analysis && (
        <div className="reports">
          <h2>Analysis for {analysis.ticker}</h2>
          <p>Date: {analysis.date}</p>
          <p>Execution time: {analysis.execution_time.toFixed(2)}s</p>

          {analysis.reports.market_report && (
            <section>
              <h3>Market Analysis</h3>
              <div>{analysis.reports.market_report.content}</div>
            </section>
          )}

          {analysis.reports.news_report && (
            <section>
              <h3>News Analysis</h3>
              <div>{analysis.reports.news_report.content}</div>
            </section>
          )}

          {analysis.reports.sentiment_report && (
            <section>
              <h3>Sentiment Analysis</h3>
              <div>{analysis.reports.sentiment_report.content}</div>
            </section>
          )}

          {analysis.reports.fundamentals_report && (
            <section>
              <h3>Fundamentals Analysis</h3>
              <div>{analysis.reports.fundamentals_report.content}</div>
            </section>
          )}
        </div>
      )}
    </div>
  );
}
```

---

### Vue 3 with TypeScript

#### Composable

```typescript
// composables/useTradingAgentsApi.ts
import { ref } from 'vue';
import type { AnalyzeResponse, RunAgentsResponse, HealthResponse } from '@/types/tradingagents-api';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

export function useTradingAgentsApi() {
  const loading = ref(false);
  const error = ref<string | null>(null);

  const analyzeStock = async (ticker: string, date: string): Promise<AnalyzeResponse> => {
    loading.value = true;
    error.value = null;

    try {
      const response = await fetch(`${API_BASE_URL}/api/v1/analyze`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ ticker, date }),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Analysis failed');
      }

      return await response.json();
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Unknown error';
      error.value = message;
      throw err;
    } finally {
      loading.value = false;
    }
  };

  const runAgents = async (
    ticker: string,
    date: string,
    agents?: string[]
  ): Promise<RunAgentsResponse> => {
    loading.value = true;
    error.value = null;

    try {
      const response = await fetch(`${API_BASE_URL}/api/v1/agents/run`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ ticker, date, agents }),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Agent execution failed');
      }

      return await response.json();
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Unknown error';
      error.value = message;
      throw err;
    } finally {
      loading.value = false;
    }
  };

  const checkHealth = async (): Promise<boolean> => {
    try {
      const response = await fetch(`${API_BASE_URL}/api/v1/health`);
      const data: HealthResponse = await response.json();
      return data.status === 'ok';
    } catch {
      return false;
    }
  };

  return {
    analyzeStock,
    runAgents,
    checkHealth,
    loading,
    error,
  };
}
```

#### Component Example

```vue
<!-- components/StockAnalysis.vue -->
<template>
  <div class="stock-analysis">
    <div class="controls">
      <input
        v-model="ticker"
        type="text"
        placeholder="Ticker (e.g., AAPL)"
        @input="ticker = $event.target.value.toUpperCase()"
      />
      <input v-model="date" type="date" />
      <button @click="handleAnalyze" :disabled="loading">
        {{ loading ? 'Analyzing...' : 'Analyze' }}
      </button>
    </div>

    <div v-if="error" class="error">Error: {{ error }}</div>

    <div v-if="analysis" class="reports">
      <h2>Analysis for {{ analysis.ticker }}</h2>
      <p>Date: {{ analysis.date }}</p>
      <p>Execution time: {{ analysis.execution_time.toFixed(2) }}s</p>

      <section v-if="analysis.reports.market_report">
        <h3>Market Analysis</h3>
        <div>{{ analysis.reports.market_report.content }}</div>
      </section>

      <section v-if="analysis.reports.news_report">
        <h3>News Analysis</h3>
        <div>{{ analysis.reports.news_report.content }}</div>
      </section>

      <section v-if="analysis.reports.sentiment_report">
        <h3>Sentiment Analysis</h3>
        <div>{{ analysis.reports.sentiment_report.content }}</div>
      </section>

      <section v-if="analysis.reports.fundamentals_report">
        <h3>Fundamentals Analysis</h3>
        <div>{{ analysis.reports.fundamentals_report.content }}</div>
      </section>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue';
import { useTradingAgentsApi } from '@/composables/useTradingAgentsApi';
import type { AnalyzeResponse } from '@/types/tradingagents-api';

const ticker = ref('AAPL');
const date = ref(new Date().toISOString().split('T')[0]);
const analysis = ref<AnalyzeResponse | null>(null);
const { analyzeStock, loading, error } = useTradingAgentsApi();

const handleAnalyze = async () => {
  try {
    analysis.value = await analyzeStock(ticker.value, date.value);
  } catch (err) {
    console.error('Analysis failed:', err);
  }
};
</script>
```

---

### Vanilla JavaScript

```javascript
// api/tradingagents.js
const API_BASE_URL = 'http://localhost:8000';

class TradingAgentsAPI {
  async analyzeStock(ticker, date, config = {}) {
    const response = await fetch(`${API_BASE_URL}/api/v1/analyze`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ ticker, date, config }),
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Analysis failed');
    }

    return await response.json();
  }

  async runAgents(ticker, date, agents = null, config = {}) {
    const response = await fetch(`${API_BASE_URL}/api/v1/agents/run`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ ticker, date, agents, config }),
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Agent execution failed');
    }

    return await response.json();
  }

  async getCachedAnalysis(ticker, date) {
    const response = await fetch(
      `${API_BASE_URL}/api/v1/analyses/${ticker}/${date}`
    );

    if (!response.ok) {
      if (response.status === 404) {
        return null; // No cached result
      }
      const error = await response.json();
      throw new Error(error.detail || 'Failed to get cached analysis');
    }

    return await response.json();
  }

  async checkHealth() {
    const response = await fetch(`${API_BASE_URL}/api/v1/health`);
    const data = await response.json();
    return data.status === 'ok';
  }
}

// Usage
const api = new TradingAgentsAPI();

async function analyzeStock() {
  const ticker = document.getElementById('ticker').value.toUpperCase();
  const date = document.getElementById('date').value;

  try {
    const result = await api.analyzeStock(ticker, date);
    displayResults(result);
  } catch (error) {
    console.error('Analysis failed:', error);
    alert(`Error: ${error.message}`);
  }
}

function displayResults(data) {
  const container = document.getElementById('results');
  container.innerHTML = `
    <h2>Analysis for ${data.ticker}</h2>
    <p>Date: ${data.date}</p>
    <p>Execution time: ${data.execution_time.toFixed(2)}s</p>
    
    ${data.reports.market_report ? `
      <section>
        <h3>Market Analysis</h3>
        <div>${data.reports.market_report.content}</div>
      </section>
    ` : ''}
    
    ${data.reports.news_report ? `
      <section>
        <h3>News Analysis</h3>
        <div>${data.reports.news_report.content}</div>
      </section>
    ` : ''}
    
    ${data.reports.sentiment_report ? `
      <section>
        <h3>Sentiment Analysis</h3>
        <div>${data.reports.sentiment_report.content}</div>
      </section>
    ` : ''}
    
    ${data.reports.fundamentals_report ? `
      <section>
        <h3>Fundamentals Analysis</h3>
        <div>${data.reports.fundamentals_report.content}</div>
      </section>
    ` : ''}
  `;
}
```

---

### Next.js

#### API Route (Server-side)

```typescript
// app/api/trading-agents/analyze/route.ts
import { NextRequest, NextResponse } from 'next/server';

const API_BASE_URL = process.env.TRADINGAGENTS_API_URL || 'http://localhost:8000';

export async function POST(request: NextRequest) {
  try {
    const body = await request.json();
    
    const response = await fetch(`${API_BASE_URL}/api/v1/analyze`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
    });

    if (!response.ok) {
      const error = await response.json();
      return NextResponse.json(
        { error: error.detail || 'Analysis failed' },
        { status: response.status }
      );
    }

    const data = await response.json();
    return NextResponse.json(data);
  } catch (error) {
    return NextResponse.json(
      { error: 'Internal server error' },
      { status: 500 }
    );
  }
}

// CORS handling
export async function OPTIONS() {
  return new NextResponse(null, {
    status: 200,
    headers: {
      'Access-Control-Allow-Origin': '*',
      'Access-Control-Allow-Methods': 'POST, OPTIONS',
      'Access-Control-Allow-Headers': 'Content-Type',
    },
  });
}
```

#### Client Component

```typescript
// components/StockAnalysisClient.tsx
'use client';

import { useState } from 'react';

export default function StockAnalysisClient() {
  const [ticker, setTicker] = useState('AAPL');
  const [date, setDate] = useState(new Date().toISOString().split('T')[0]);
  const [analysis, setAnalysis] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const handleAnalyze = async () => {
    setLoading(true);
    setError(null);

    try {
      const response = await fetch('/api/trading-agents/analyze', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ ticker, date }),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.error || 'Analysis failed');
      }

      const data = await response.json();
      setAnalysis(data);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div>
      {/* Form and results display similar to React example */}
    </div>
  );
}
```

---

## Error Handling

### Standard Error Response

All API errors follow this format:

```typescript
interface ApiError {
  error: string;
  detail?: string;
  timestamp: string;
}
```

### Common HTTP Status Codes

- `200` - Success
- `400` - Bad Request (invalid parameters)
- `404` - Not Found (cached analysis not available)
- `500` - Internal Server Error

### Error Handling Example

```typescript
async function analyzeWithErrorHandling(ticker: string, date: string) {
  try {
    const response = await fetch(`${API_BASE_URL}/api/v1/analyze`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ ticker, date }),
    });

    if (!response.ok) {
      const errorData: ApiError = await response.json();
      
      switch (response.status) {
        case 400:
          throw new Error(`Invalid request: ${errorData.detail}`);
        case 404:
          throw new Error('Analysis not found');
        case 500:
          throw new Error(`Server error: ${errorData.detail}`);
        default:
          throw new Error(errorData.error || 'Unknown error');
      }
    }

    return await response.json();
  } catch (error) {
    if (error instanceof TypeError) {
      // Network error
      console.error('Network error:', error);
      throw new Error('Unable to connect to API server');
    }
    throw error;
  }
}
```

## CORS Configuration

The API server is configured with CORS middleware that allows all origins by default:

```python
# In tradingagents/api/server.py
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify allowed origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### Production CORS Setup

For production, update the server configuration to allow only your frontend domain:

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://yourdomain.com",
        "https://www.yourdomain.com",
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type", "Accept"],
)
```

## Best Practices

### 1. Environment Variables

Use environment variables for API configuration:

```typescript
// .env.local
REACT_APP_API_BASE_URL=http://localhost:8000

// .env.production
REACT_APP_API_BASE_URL=https://api.yourdomain.com
```

### 2. Request Timeout

Add timeout handling:

```typescript
const controller = new AbortController();
const timeoutId = setTimeout(() => controller.abort(), 30000); // 30 seconds

try {
  const response = await fetch(`${API_BASE_URL}/api/v1/analyze`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ ticker, date }),
    signal: controller.signal,
  });
  clearTimeout(timeoutId);
  // ... handle response
} catch (error) {
  if (error.name === 'AbortError') {
    throw new Error('Request timeout');
  }
  throw error;
}
```

### 3. Retry Logic

Implement retry for transient failures:

```typescript
async function fetchWithRetry(
  url: string,
  options: RequestInit,
  maxRetries = 3
): Promise<Response> {
  for (let i = 0; i < maxRetries; i++) {
    try {
      const response = await fetch(url, options);
      if (response.ok || response.status !== 500) {
        return response;
      }
    } catch (error) {
      if (i === maxRetries - 1) throw error;
      await new Promise(resolve => setTimeout(resolve, 1000 * (i + 1)));
    }
  }
  throw new Error('Max retries exceeded');
}
```

### 4. Date Format Validation

Validate date format before sending:

```typescript
function isValidDate(dateString: string): boolean {
  const regex = /^\d{4}-\d{2}-\d{2}$/;
  if (!regex.test(dateString)) return false;
  
  const date = new Date(dateString);
  return date instanceof Date && !isNaN(date.getTime());
}

if (!isValidDate(date)) {
  throw new Error('Invalid date format. Use YYYY-MM-DD');
}
```

### 5. Loading States

Always provide user feedback during API calls:

```typescript
const [loading, setLoading] = useState(false);
const [error, setError] = useState<string | null>(null);

async function handleAnalyze() {
  setLoading(true);
  setError(null);
  
  try {
    const result = await analyzeStock(ticker, date);
    // Handle success
  } catch (err) {
    setError(err.message);
  } finally {
    setLoading(false);
  }
}
```

### 6. Cache Management

Check for cached results before making new requests:

```typescript
async function getAnalysisWithCache(ticker: string, date: string) {
  // Try cached first
  try {
    const cached = await fetch(
      `${API_BASE_URL}/api/v1/analyses/${ticker}/${date}`
    );
    if (cached.ok) {
      return await cached.json();
    }
  } catch {
    // Ignore cache errors, proceed to fresh analysis
  }

  // If no cache, run fresh analysis
  return await analyzeStock(ticker, date);
}
```

## Complete Example

A complete working example for React:

```typescript
// CompleteExample.tsx
import React, { useState } from 'react';

interface AnalyzeResponse {
  ticker: string;
  date: string;
  reports: {
    market_report?: { content: string; timestamp?: string };
    sentiment_report?: { content: string; timestamp?: string };
    news_report?: { content: string; timestamp?: string };
    fundamentals_report?: { content: string; timestamp?: string };
  };
  execution_time: number;
  timestamp: string;
}

const API_BASE_URL = 'http://localhost:8000';

export function CompleteExample() {
  const [ticker, setTicker] = useState('AAPL');
  const [date, setDate] = useState(new Date().toISOString().split('T')[0]);
  const [analysis, setAnalysis] = useState<AnalyzeResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleAnalyze = async () => {
    setLoading(true);
    setError(null);

    try {
      const response = await fetch(`${API_BASE_URL}/api/v1/analyze`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ ticker, date }),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Analysis failed');
      }

      const data: AnalyzeResponse = await response.json();
      setAnalysis(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{ padding: '20px' }}>
      <h1>Stock Analysis</h1>
      
      <div style={{ marginBottom: '20px' }}>
        <input
          type="text"
          value={ticker}
          onChange={(e) => setTicker(e.target.value.toUpperCase())}
          placeholder="Ticker"
          style={{ marginRight: '10px', padding: '8px' }}
        />
        <input
          type="date"
          value={date}
          onChange={(e) => setDate(e.target.value)}
          style={{ marginRight: '10px', padding: '8px' }}
        />
        <button
          onClick={handleAnalyze}
          disabled={loading}
          style={{ padding: '8px 16px' }}
        >
          {loading ? 'Analyzing...' : 'Analyze'}
        </button>
      </div>

      {error && (
        <div style={{ color: 'red', marginBottom: '20px' }}>
          Error: {error}
        </div>
      )}

      {analysis && (
        <div>
          <h2>Analysis for {analysis.ticker}</h2>
          <p>Date: {analysis.date}</p>
          <p>Execution Time: {analysis.execution_time.toFixed(2)}s</p>

          {analysis.reports.market_report && (
            <section style={{ marginTop: '20px' }}>
              <h3>Market Analysis</h3>
              <pre style={{ whiteSpace: 'pre-wrap' }}>
                {analysis.reports.market_report.content}
              </pre>
            </section>
          )}

          {analysis.reports.news_report && (
            <section style={{ marginTop: '20px' }}>
              <h3>News Analysis</h3>
              <pre style={{ whiteSpace: 'pre-wrap' }}>
                {analysis.reports.news_report.content}
              </pre>
            </section>
          )}

          {analysis.reports.sentiment_report && (
            <section style={{ marginTop: '20px' }}>
              <h3>Sentiment Analysis</h3>
              <pre style={{ whiteSpace: 'pre-wrap' }}>
                {analysis.reports.sentiment_report.content}
              </pre>
            </section>
          )}

          {analysis.reports.fundamentals_report && (
            <section style={{ marginTop: '20px' }}>
              <h3>Fundamentals Analysis</h3>
              <pre style={{ whiteSpace: 'pre-wrap' }}>
                {analysis.reports.fundamentals_report.content}
              </pre>
            </section>
          )}
        </div>
      )}
    </div>
  );
}
```

## Additional Resources

- **API Documentation**: Visit `http://localhost:8000/docs` for interactive Swagger UI
- **ReDoc Documentation**: Visit `http://localhost:8000/redoc` for alternative API docs
- **Health Check**: `GET /api/v1/health` to verify API availability

## Support

For issues or questions:
1. Check the API health endpoint
2. Review server logs
3. Verify CORS configuration
4. Ensure date format is YYYY-MM-DD
5. Check ticker symbol is valid

