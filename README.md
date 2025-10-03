# Paperly API Gateway - Academic Papers Navigation Platform

**Case Study #6 - Software Architecture - UTEC 2025-II**

A FastAPI-based academic papers navigation platform implementing microservices architecture patterns with comprehensive fitness functions monitoring.

## Architecture Overview

```
┌─────────────────┐
│   API Gateway   │ ← FastAPI (Port 3000)
│   (Main App)    │
└────────┬────────┘
         │
    ┌────┴────┬──────────┬──────────┐
    │         │          │          │
┌───▼────┐ ┌─▼──────┐ ┌─▼────────┐ ┌▼────────┐
│ Search │ │Citation │ │Quality   │ │ Cache/  │
│Service │ │ Graph   │ │Control   │ │Storage  │
│(Mock)  │ │(Mock)   │ │(Mock)    │ │(SQLite) │
└────────┘ └─────────┘ └──────────┘ └─────────┘
```

## Features Implemented

### Core Functionality
- **Authentication**: JWT-based auth with role-based access (student/admin)
- **Paper Search**: Full-text search with filters (author, year, keywords, open access)
- **Paper Management**: CRUD operations, metadata extraction, quality validation
- **Citation Graph**: Simulated citation relationships and graph analysis
- **Personal Library**: Save papers with tags and notes
- **Recommendations**: 4 strategies (similarity, collaborative, citation, hybrid)

### Advanced Features
- **Distributed Cache**: Simulated Redis-like caching system
- **Quality Control**: Automated metadata validation with scoring
- **PDF Processing**: Mock PDF upload and metadata extraction
- **External APIs**: Mock integrations (CrossRef, IEEE, Semantic Scholar)
- **Web Scraping**: Mock arXiv and Google Scholar scrapers
- **Export Formats**: 6 citation formats (BibTeX, APA, Chicago, IEEE, MLA, Harvard)

### Monitoring & Performance
- **Fitness Functions**: Automated architecture compliance monitoring
- **Structured Logging**: JSON logs with request tracing
- **Performance Metrics**: Prometheus-compatible metrics
- **Health Checks**: Comprehensive system status monitoring
- **Rate Limiting**: Tiered limits (anonymous: 50/min, student: 200/min, admin: 1000/min)

## Fitness Functions

### 1. Search Performance
- **Threshold**: < 3000ms response time
- **Monitoring**: Real-time search latency tracking
- **Violation Tolerance**: 50% for POC environment

### 2. Data Integrity
- **Threshold**: ≥ 95% metadata consistency
- **Validation**: Title, authors, DOI, year, citation links
- **Citation Graph**: ≥ 98% valid edge integrity

### 3. Additional Metrics
- Gateway response time < 1000ms
- Cache hit rate > 80%
- Uptime ≥ 99.9%
- Ingest performance > 50 papers/hour

## Quick Start

### Prerequisites
- Python 3.11+
- SQLite (included)

### Installation
```bash
# Clone repository
git clone <repository-url>
cd paperly-api-gateway

# Install dependencies
pip install -r requirements.txt

# Start application
python main.py
```

### Access Points
- **API Documentation**: http://localhost:3000/api/docs
- **Health Check**: http://localhost:3000/api/v1/health
- **Metrics**: http://localhost:3000/metrics
- **Main API**: http://localhost:3000/api/v1/

## Test Credentials

```
Student Account:
Email: student@utec.edu.pe
Password: password123

Admin Account:  
Email: admin@utec.edu.pe
Password: admin123
```

## API Endpoints

### Authentication
- `POST /api/v1/auth/login` - User authentication
- `GET /api/v1/auth/profile` - User profile

### Search & Papers
- `GET /api/v1/search` - Search papers with filters
- `GET /api/v1/search/autocomplete` - Search suggestions
- `GET /api/v1/papers/{id}` - Paper details
- `GET /api/v1/papers/{id}/recommendations` - Paper recommendations
- `GET /api/v1/papers/{id}/citation-graph` - Citation network
- `POST /api/v1/papers/upload` - Upload PDF papers
- `GET /api/v1/papers/{id}/export` - Export citations

### Personal Library
- `GET /api/v1/library` - User's saved papers
- `POST /api/v1/library/papers/{id}` - Save paper
- `DELETE /api/v1/library/papers/{id}` - Remove paper
- `GET /api/v1/library/tags` - User's tags

### Administration
- `POST /api/v1/admin/ingest/batch` - Batch paper ingestion
- `GET /api/v1/admin/stats/system` - System statistics
- `GET /api/v1/admin/cache/stats` - Cache performance

### Monitoring
- `GET /api/v1/health` - System health
- `GET /api/v1/health/fitness` - Fitness functions status
- `GET /metrics` - Prometheus metrics

## Project Structure

```
paperly-api-gateway/
├── main.py                    # FastAPI application entry point
├── config.py                  # Configuration settings
├── requirements.txt           # Python dependencies
├── paperly.db                # SQLite database (auto-created)
│
├── database/
│   ├── database.py           # Database models and connection
│   └── operations.py         # Database operations
│
├── models/
│   └── auth.py               # Authentication models
│
├── routers/
│   ├── auth.py               # Authentication endpoints
│   ├── search.py             # Search endpoints
│   ├── papers.py             # Paper management endpoints
│   ├── library.py            # Personal library endpoints
│   ├── health.py             # Health check endpoints
│   └── admin.py              # Administration endpoints
│
├── services/
│   ├── cache_service.py      # Distributed caching
│   ├── recommendation_service.py # Paper recommendations
│   ├── citation_service.py   # Citation graph analysis
│   ├── quality_service.py    # Quality control validation
│   ├── external_apis.py      # External API integrations
│   ├── scraper_service.py    # Web scraping services
│   ├── pdf_service.py        # PDF processing
│   └── storage_service.py    # Distributed storage
│
├── middleware/
│   ├── logging.py            # Structured logging
│   └── rate_limit.py         # Rate limiting
│
└── .github/
    └── workflows/
        └── fitness-functions.yml # CI/CD fitness functions
```

## Sample Data

The application includes 4 pre-loaded academic papers:

1. **"Human-level control through deep reinforcement learning"** (Nature, 2015)
2. **"Attention Is All You Need"** (arXiv, 2017)
3. **"Playing Atari with Deep Reinforcement Learning"** (Science, 2013)
4. **"Mastering the game of Go with deep neural networks"** (Nature, 2016)

## Development Commands

```bash
# Start development server
python main.py

# Run fitness function tests locally
python test_fitness.py

# Check health status
curl http://localhost:3000/api/v1/health

# Test authentication
curl -X POST http://localhost:3000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "student@utec.edu.pe", "password": "password123"}'

# Search papers
curl "http://localhost:3000/api/v1/search?q=machine%20learning" \
  -H "Authorization: Bearer <YOUR_TOKEN>"
```

## CI/CD Integration

### GitHub Actions Fitness Functions

The project includes automated fitness function testing via GitHub Actions:

- **Triggers**: Push, PR, scheduled (every 6 hours)
- **Tests**: Search performance, data integrity
- **Reports**: Detailed summaries in GitHub Step Summary
- **Thresholds**: Configurable for different environments

### Workflow Configuration

1. Place `.github/workflows/fitness-functions.yml` in your repository
2. Push to trigger automated testing
3. View results in GitHub Actions tab
4. Monitor fitness function compliance over time

## Architecture Compliance

### Implemented Patterns
- **Microservices**: Simulated service separation
- **Load Balancing**: Rate limiting and request distribution
- **Distributed Cache**: Memory-based caching with TTL
- **Quality Control**: Automated validation pipelines
- **Monitoring**: Comprehensive health and performance tracking

### Fitness Functions Coverage
- ✅ **Performance**: Search latency < 3000ms
- ✅ **Reliability**: Data integrity ≥ 95%
- ✅ **Availability**: Health monitoring with uptime tracking
- ✅ **Scalability**: Rate limiting and resource management

## Production Considerations

### Security
- JWT token expiration (7 days)
- Rate limiting by user tier
- Input validation and sanitization
- CORS configuration

### Performance
- Database query optimization
- Response caching strategies
- Async request handling
- Connection pooling

### Monitoring
- Structured JSON logging
- Performance metrics collection
- Error tracking and alerting
- Health check endpoints

## Contributing

1. Fork the repository
2. Create a feature branch
3. Implement changes with tests
4. Ensure fitness functions pass
5. Submit pull request

## Team

**GYKTEAM**
- Adrian Antonio Auqui Perez
- Jose Barrenchea Merino

**Institution**: Universidad de Ingeniería y Tecnología (UTEC)
**Course**: Software Architecture - 2025-II
**Case Study**: #6 - Academic Papers Navigation Platform

---

**Note**: This is a Proof of Concept (POC) implementation focusing on architecture patterns and fitness functions. External integrations are mocked for demonstration purposes.