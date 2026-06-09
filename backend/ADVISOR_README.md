# FINsim Virtual Advisor API

FastAPI server for on-demand tactical advice analysis of financial metrics using Ollama (qwen2.5:3b).

## Quick Start

### 1. Install Dependencies

```bash
pip install -r advisor_requirements.txt
```

### 2. Ollama is running on 10.12.7.53:11434

Make sure you have access to the Ollama server on that IP.

### 3. Run the API Server

```bash
cd /home/elisa/FINsim_v2/backend
python advisor_standalone.py
```

The API will start on `http://localhost:8000`

**Interactive Docs:** Open `http://localhost:8000/docs` in your browser

## API Endpoints

### POST `/api/advisor/chat`
Generate tactical advice from financial metrics.

**Request:**
```json
{
  "metrics_data": {
    "performance_metrics": {"adaptive": 85, "benchmark": 70},
    "client_engagement": {"active_clients": 45, "trust_score": 7.2},
    "product_distribution": {"bonds": 40, "equity": 35, "derivatives": 25},
    "market_conditions": {"sentiment": "cautious", "rate_trend": "rising"},
    "heatmap_data": {
      "segment_A": {"performance": 90},
      "segment_B": {"performance": 65}
    }
  },
  "user_message": "What actions should I take this round?"
}
```

**Response:**
```json
{
  "suggerimento_breve": "Increase bond allocation for segment B; boost engagement through personalized recommendations.",
  "dettaglio_risposta": "Performance analysis reveals a 25-point gap between segments. Segment A shows strong engagement (85% active), while segment B lags at 65%. The rising rate environment favors bonds. Recommend reallocating 15% of segment B portfolio from equities to bonds and launching targeted contact campaign.",
  "grafici_consigliati": [
    "HEATMAP_PERFORMANCE",
    "BAR_PRODOTTI",
    "MOMENTUM_TIMELINE"
  ]
}
```

### GET `/health`
Health check endpoint.

**Response:**
```json
{
  "status": "ok",
  "service": "FINsim Virtual Advisor API",
  "llm_model": "qwen2.5:3b"
}
```

### GET `/api/advisor/charts`
List available chart codes the advisor can recommend.

**Response:**
```json
{
  "available_charts": [
    {
      "code": "HEATMAP_PERFORMANCE",
      "description": "Performance intensity by client/product segment"
    },
    {
      "code": "MOMENTUM_TIMELINE",
      "description": "Trend strength and reversals over time"
    },
    {
      "code": "BAR_PRODOTTI",
      "description": "Product distribution and mix analysis"
    },
    {
      "code": "KPI_MACRO",
      "description": "Macro KPI indicators and benchmarks"
    }
  ]
}
```

### GET `/docs`
API documentation with usage examples.

## Key Features

✅ **JSON-Forced Output** — Uses Ollama's `format: json` parameter to guarantee structured responses  
✅ **Robust Parsing** — Extracts valid JSON even if model adds extra text  
✅ **Chart Validation** — Filters recommendations to allowed codes only  
✅ **120s Timeout** — Configurable timeout for long-running analyses  
✅ **Error Handling** — Clean HTTP error codes: 504 (timeout), 503 (unavailable), 500 (error)  
✅ **Interactive Docs** — Swagger UI at `/docs`, ReDoc at `/redoc`  
✅ **Logging** — Detailed request/response logging for debugging  

## Configuration

### Ollama Connection
Server: `10.12.7.53:11434`

Modify in `advisor_standalone.py` if needed:
```python
class OllamaAdvisor:
    OLLAMA_GENERATE_URL = "http://10.12.7.53:11434/api/generate"
    OLLAMA_TIMEOUT = 120  # seconds
    MODEL_NAME = "qwen2.5:3b"
```

### Server Settings
When running via `python advisor_standalone.py`:
- Host: `0.0.0.0`
- Port: `8000`

Or with uvicorn directly:
```bash
uvicorn advisor_standalone:app --host 0.0.0.0 --port 8000 --reload
```

## Testing with curl

### Empty message (initial tactical summary):
```bash
curl -X POST http://localhost:8000/api/advisor/chat \
  -H "Content-Type: application/json" \
  -d '{
    "metrics_data": {
      "performance_metrics": {"adaptive": 82, "benchmark": 70},
      "client_engagement": {"active": 42}
    },
    "user_message": ""
  }'
```

### With specific question:
```bash
curl -X POST http://localhost:8000/api/advisor/chat \
  -H "Content-Type: application/json" \
  -d '{
    "metrics_data": {
      "performance_metrics": {"adaptive": 82, "benchmark": 70},
      "client_engagement": {"active": 42}
    },
    "user_message": "Why is segment B underperforming?"
  }'
```

### Health check:
```bash
curl http://localhost:8000/health
```

## Integration with Frontend

The API is designed for on-demand calls from your frontend:

```javascript
// Example frontend call (JavaScript/React)
const response = await fetch('http://localhost:8000/api/advisor/chat', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    metrics_data: metricsFromDatabase,
    user_message: userQuestion || ""
  })
});

const advice = await response.json();

// Use advice.grafici_consigliati to show appropriate charts
if (advice.grafici_consigliati.includes('HEATMAP_PERFORMANCE')) {
  showHeatmapChart();
}
if (advice.grafici_consigliati.includes('MOMENTUM_TIMELINE')) {
  showMomentumChart();
}
// ... etc
```

## Troubleshooting

**"LLM service unavailable" (503)**
- Ensure Ollama is running on `10.12.7.53:11434`
- Check connection: `curl http://10.12.7.53:11434/api/tags`
- Check network connectivity to that IP

**"LLM request timed out" (504)**
- Increase `OLLAMA_TIMEOUT` in `advisor_standalone.py` (default 120s)
- Ensure Ollama has enough resources
- Check if the model is running: Check Ollama status on 10.12.7.53

**"LLM response format invalid" (500)**
- Verify qwen2.5:3b is available on the Ollama server
- Check Ollama server logs
- Ensure valid JSON is being returned

**Empty metrics_data issue**
- Always include at least basic metrics: `{"round": 1}`
- More complete metrics lead to better advice

## Files

- `advisor_standalone.py` — Complete standalone FastAPI server (ready to run)
- `advisor_requirements.txt` — Python dependencies
- `app/finsim/advisor.py` — Project-integrated version (for Flask integration)

## Notes

- The advisor uses **Italian language** for all responses (per system prompt)
- Response includes 3 fields: short tactical suggestion, detailed explanation, recommended charts
- Each request calls Ollama independently (stateless design)
- No database required — metrics passed directly in request
- 120-second timeout prevents indefinite hangs
- Ollama server: `10.12.7.53:11434`
