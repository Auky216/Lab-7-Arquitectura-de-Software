# main.py
import time
import uuid
import multiprocessing
from contextlib import asynccontextmanager
from fastapi.responses import ORJSONResponse
from functools import lru_cache

import structlog
import uvicorn
from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST, REGISTRY
from starlette.responses import Response

from routers import auth, search, papers, library, health
from middleware.logging import setup_logging
from config import settings
from database.database import init_db, engine

# Setup structured logging
setup_logging()
logger = structlog.get_logger()

# Prometheus metrics
try:
    REQUEST_COUNT = REGISTRY._names_to_collectors.get('http_requests_total')
    REQUEST_DURATION = REGISTRY._names_to_collectors.get('http_request_duration_seconds')
    FITNESS_VIOLATIONS = REGISTRY._names_to_collectors.get('fitness_function_violations_total')
except:
    REQUEST_COUNT = None
    REQUEST_DURATION = None
    FITNESS_VIOLATIONS = None

if REQUEST_COUNT is None:
    REQUEST_COUNT = Counter('http_requests_total', 'Total HTTP requests', ['method', 'endpoint', 'status'])
if REQUEST_DURATION is None:
    REQUEST_DURATION = Histogram('http_request_duration_seconds', 'HTTP request duration', ['method', 'endpoint'])
if FITNESS_VIOLATIONS is None:
    FITNESS_VIOLATIONS = Counter('fitness_function_violations_total', 'Fitness function violations', ['function', 'endpoint'])

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("🚀 Paperly API Gateway starting up")
    logger.info("🗄️ Initializing PostgreSQL database...")
    
    try:
        await init_db()
        logger.info("✅ Database initialized successfully")
    except Exception as e:
        logger.error("❌ Database initialization failed", error=str(e))
        raise
    
    logger.info("🌟 API Gateway ready to serve requests")
    yield
    
    # Shutdown - cerrar conexiones limpiamente
    await engine.dispose()
    logger.info("🛑 Paperly API Gateway shutting down")

# Create FastAPI with optimizations
app = FastAPI(
    title="Paperly API Gateway",
    description="Academic Papers Navigation Platform - High Performance",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    lifespan=lifespan,
    default_response_class=ORJSONResponse  # JSON más rápido
)

# Security middleware
app.add_middleware(TrustedHostMiddleware, allowed_hosts=["*"])

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173", "http://127.0.0.1:3000", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.middleware("http")
async def logging_and_metrics_middleware(request: Request, call_next):
    start_time = time.time()
    request_id = str(uuid.uuid4())
    request.state.request_id = request_id
    
    try:
        response = await call_next(request)
        duration = time.time() - start_time
        duration_ms = duration * 1000
        
        # Record metrics
        try:
            endpoint = request.url.path
            REQUEST_COUNT.labels(method=request.method, endpoint=endpoint, status=response.status_code).inc()
            REQUEST_DURATION.labels(method=request.method, endpoint=endpoint).observe(duration)
        except:
            pass
        
        # Fitness checks
        fitness_checks_passed = True
        
        if "/search" in endpoint and duration_ms > 200:
            try:
                FITNESS_VIOLATIONS.labels(function="search_response_time", endpoint=endpoint).inc()
            except:
                pass
            fitness_checks_passed = False
        
        if "/papers/" in endpoint and request.method == "GET" and duration_ms > 100:
            try:
                FITNESS_VIOLATIONS.labels(function="catalog_response_time", endpoint=endpoint).inc()
            except:
                pass
            fitness_checks_passed = False
        
        if duration_ms > 1000:
            try:
                FITNESS_VIOLATIONS.labels(function="gateway_response_time", endpoint=endpoint).inc()
            except:
                pass
            fitness_checks_passed = False
        
        # Add headers
        response.headers["X-Request-ID"] = request_id
        response.headers["X-Response-Time"] = f"{duration_ms:.2f}ms"
        response.headers["X-Fitness-Status"] = "PASS" if fitness_checks_passed else "VIOLATION"
        
        return response
        
    except Exception as e:
        duration = time.time() - start_time
        duration_ms = duration * 1000
        logger.error("❌ Request failed", method=request.method, url=str(request.url), error=str(e), duration_ms=round(duration_ms, 2), request_id=request_id)
        raise

# Include routers
app.include_router(auth.router, prefix="/api/v1/auth", tags=["Authentication"])
app.include_router(search.router, prefix="/api/v1/search", tags=["Search"])
app.include_router(papers.router, prefix="/api/v1/papers", tags=["Papers"])
app.include_router(library.router, prefix="/api/v1/library", tags=["Library"])
app.include_router(health.router, prefix="/api/v1/health", tags=["Health & Monitoring"])

@app.get("/metrics")
async def prometheus_metrics():
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)

@app.get("/")
async def root():
    return {
        "service": "Paperly API Gateway",
        "version": "1.0.0",
        "description": "Academic Papers Navigation Platform - High Performance",
        "database": "PostgreSQL",
        "fitness_functions": ["Search response time < 200ms", "Catalog rendering < 100ms", "Gateway response < 1000ms"],
        "endpoints": {
            "docs": "/api/docs",
            "redoc": "/api/redoc",
            "health": "/api/v1/health",
            "metrics": "/metrics",
            "auth": "/api/v1/auth/login",
            "search": "/api/v1/search",
            "papers": "/api/v1/papers/{id}",
            "library": "/api/v1/library"
        },
        "test_credentials": {
            "student": "student@utec.edu.pe / password123",
            "admin": "admin@utec.edu.pe / admin123"
        },
        "timestamp": time.time()
    }

@app.get("/api/v1/status")
async def api_status():
    try:
        from database.database import AsyncSessionLocal
        from sqlalchemy import text
        
        db_status = "up"
        paper_count = 0
        user_count = 0
        
        try:
            async with AsyncSessionLocal() as session:
                await session.execute(text("SELECT 1"))
                result = await session.execute(text("SELECT COUNT(*) FROM papers"))
                paper_count = result.scalar() or 0
                result = await session.execute(text("SELECT COUNT(*) FROM users"))
                user_count = result.scalar() or 0
        except Exception as e:
            db_status = "down"
            logger.error("Database status check failed", error=str(e))
        
        return {
            "api_status": "operational",
            "database": {
                "status": db_status,
                "type": "PostgreSQL",
                "papers_count": paper_count,
                "users_count": user_count
            },
            "fitness_functions": {
                "search_latency": {"threshold": "< 200ms", "status": "monitored"},
                "catalog_rendering": {"threshold": "< 100ms", "status": "monitored"},
                "gateway_performance": {"threshold": "< 1000ms", "status": "monitored"}
            },
            "features": {
                "authentication": "enabled",
                "paper_search": "enabled",
                "personal_library": "enabled"
            }
        }
    except Exception as e:
        logger.error("Status check failed", error=str(e))
        raise HTTPException(status_code=500, detail="Status check failed")

@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    return ORJSONResponse(status_code=exc.status_code, content={"error": exc.detail})

@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    return ORJSONResponse(status_code=500, content={"error": "Internal server error"})

if __name__ == "__main__":
    print("🚀 Starting Paperly API Gateway...")
    print("📚 Academic Papers Navigation Platform")
    print("🗄️ Database: PostgreSQL")
    print("🎯 Fitness Functions: Active")
    print("📊 Monitoring: Enabled")
    print("=" * 50)
    
    # Calcular workers óptimos
    workers = (multiprocessing.cpu_count() * 2) + 1
    
    print(f"⚡ Workers: {workers}")
    print(f"🔥 Ready for high concurrency")
    
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=3000,
        workers=workers,  # Múltiples workers
        log_level="error",  # Solo errores
        access_log=False  # Sin logs de acceso
    )