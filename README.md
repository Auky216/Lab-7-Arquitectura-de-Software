🚀 **Academic Papers Navigation Platform - Proof of Concept**

## Features

### ✅ Implemented
- **Authentication**: JWT + Mock SSO
- **Search**: Paper search with filters
- **Papers**: Details, citations, references, recommendations
- **Library**: Personal paper management
- **Health**: Service monitoring
- **Fitness Functions**: Automated performance monitoring

### 🎯 Fitness Functions
- Search response time < 200ms
- Catalog rendering < 100ms
- Gateway response time < 1000ms
- Rate limiting (100 req/min)
- Uptime monitoring

## Quick Start

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Start infrastructure
docker-compose up -d postgres mongodb redis elasticsearch

# 3. Start API Gateway
python main.py

# 4. Test API
curl http://localhost:3000/api/v1/health

# 5. Open docs
open http://localhost:3000/api/docs
```

## API Endpoints

### Authentication
- `POST /api/v1/auth/login` - Login
- `GET /api/v1/auth/profile` - User profile

### Search
- `GET /api/v1/search` - Search papers (< 200ms fitness)
- `GET /api/v1/search/autocomplete` - Suggestions

### Papers
- `GET /api/v1/papers/{id}` - Paper details (< 100ms fitness)
- `GET /api/v1/papers/{id}/citations` - Citations
- `GET /api/v1/papers/{id}/references` - References
- `GET /api/v1/papers/{id}/related` - Recommendations
- `POST /api/v1/papers/{id}/export` - Export reference

### Library
- `GET /api/v1/library` - Personal library
- `POST /api/v1/library/papers/{id}` - Save paper
- `DELETE /api/v1/library/papers/{id}` - Remove paper

### Monitoring
- `GET /api/v1/health` - Health check
- `GET /metrics` - Prometheus metrics

## Test Credentials

```
Email: student@utec.edu.pe
Password: password123

Email: admin@utec.edu.pe  
Password: admin123
```

## Fitness Functions Testing

```bash
# Test performance
python scripts/test_fitness_functions.py

# Monitor metrics
curl http://localhost:3000/metrics
```

## Architecture

```
┌─────────────────┐
│   API Gateway   │ ← FastAPI (Port 3000)
│   (This repo)   │
└────────┬────────┘
         │
    ┌────┴────┬──────────┬──────────┐
    │         │          │          │
┌───▼────┐ ┌─▼──────┐ ┌─▼────────┐ ┌▼────────┐
│ Search │ │Ingestion│ │ Workers  │ │ Cache/  │
│Service │ │ Service │ │ Service  │ │ DB      │
│:3001   │ │  :3002  │ │   BG     │ │ Redis   │
└────────┘ └─────────┘ └──────────┘ └─────────┘
```

## Logs Example

```json
{
  "event": "🔍 [SEARCH] Gateway received search request",
  "query": "machine learning",
  "filters": {"author": "Hinton"},
  "user": "student@utec.edu.pe",
  "timestamp": "2025-01-01T12:00:00Z"
}

{
  "event": "⚠️ [FITNESS] Search exceeded 200ms",
  "duration_ms": 250,
  "threshold": 200,
  "endpoint": "/api/v1/search",
  "request_id": "uuid-here"
}
```

## Why FastAPI > NestJS for POC?

| Aspect | FastAPI | NestJS |
|--------|---------|--------|
| Setup time | 5 mins | 30 mins |
| Code lines | 50% less | More boilerplate |
| Docs | Auto Swagger | Manual setup |
| Performance | Native async | Good |
| Learning curve | Easy | Steeper |
| **POC suitability** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ |

---

**Next Steps**: Implement Search Service and Ingestion Service using same FastAPI pattern!