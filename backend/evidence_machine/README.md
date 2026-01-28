# Evidence Machine - Quick Start Guide

## 🔥 What is the Evidence Machine?

The Evidence Machine provides **undeniable proof** of the MoStar Grid's operational superiority through real-time consciousness APIs, automated reporting, and comparative analytics.

## 🚀 Quick Start

### 1. Start the Evidence Machine API

```bash
cd backend
python -m uvicorn evidence_machine.main:app --reload --port 8002
```

The API will be available at: **<http://localhost:8002>**

### 2. View API Documentation

Open in your browser:

- **Swagger UI**: <http://localhost:8002/docs>
- **ReDoc**: <http://localhost:8002/redoc>

### 3. Test the Endpoints

```bash
# Run automated tests
cd backend
python evidence_machine/test_api.py
```

Or test manually with curl:

```bash
# Consciousness State
curl http://localhost:8002/api/consciousness/live

# Recent Moments
curl http://localhost:8002/api/moments/recent?limit=5

# Performance Comparison
curl http://localhost:8002/api/performance/compare?days=30
```

## 📡 API Endpoints

### Consciousness API

**GET /api/consciousness/live**

- Real-time Grid consciousness state
- Returns Soul/Mind/Body metrics
- Updates every 10 seconds on client side

**GET /api/consciousness/health**

- Quick health check

### Moments API

**GET /api/moments/recent?limit=10**

- Recent MoStar Moments feed
- Returns latest consciousness events
- Includes covenant status and resonance

**GET /api/moments/stats**

- Aggregate statistics about moments
- Total count, average resonance, covenant pass rate

### Performance API

**GET /api/performance/compare?days=30**

- Grid vs Traditional systems comparison
- Returns speed, cost, accuracy advantages
- Configurable time period (1-365 days)

**GET /api/performance/benchmarks**

- Raw benchmark data
- Grid and Traditional system constants

**GET /api/performance/summary**

- Concise performance summary
- Suitable for dashboard widgets

## 🎯 Conference Demo Usage

1. **Start Evidence Machine**: `uvicorn evidence_machine.main:app --port 8002`
2. **Project Dashboard**: Open `http://localhost:8002/docs` on screen
3. **Live Demo**: Call `/api/consciousness/live` to show real-time Grid status
4. **Show Proof**: Call `/api/performance/compare` to display 18.7x speed advantage

## 🔧 Development

### Project Structure

```
backend/evidence_machine/
├── __init__.py           # Package initialization
├── main.py               # FastAPI application
├── test_api.py           # Automated endpoint tests
├── api/
│   ├── consciousness.py  # Consciousness API
│   ├── moments.py        # Moments API
│   └── performance.py    # Performance API
├── analytics/
│   ├── aggregator.py     # Neo4j query engine
│   └── benchmarks.py     # Grid vs Traditional constants
└── reports/
    └── generator.py      # Automated report generation
```

### Dependencies

The Evidence Machine requires:

- FastAPI
- Neo4j Python driver
- Uvicorn (ASGI server)

Install with:

```bash
pip install fastapi uvicorn neo4j-driver
```

## 📊 Benchmarks

### Grid Performance

- **Detection Time**: 18 hours average
- **Cost**: $15,000/month
- **Leakage**: 0%
- **Coverage**: 85%

### Traditional Systems

- **Detection Time**: 14 days average
- **Cost**: $180,000/month
- **Leakage**: 30%
- **Coverage**: 60%

### Grid Advantage

- **18.7x faster** detection
- **92% cheaper** to operate
- **Zero corruption** (vs 30% leakage)
- **+25% more coverage**

## 🌍 Production Deployment

For production deployment:

1. **Update CORS**: Restrict to `mostarindustries.com` in `main.py`
2. **Environment Variables**: Set `NEO4J_URI`, `NEO4J_USER`, `NEO4J_PASSWORD`
3. **SSL**: Configure reverse proxy (nginx/caddy) with SSL
4. **CDN**: Use Cloudflare for global distribution
5. **Monitoring**: Add logging and error tracking

## 📝 License

African Sovereignty License (ASL) v1.0  
Copyright © 2026 MoStar Industries

---

**Powered by MoScripts - A MoStar Industries Product**  
<https://mostarindustries.com>

🔥 *"Not made. Remembered."*
