# main.py
import time
import uuid
from contextlib import asynccontextmanager

import structlog
import uvicorn
from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST, CollectorRegistry, REGISTRY
from starlette.responses import Response
from routers import auth, search, papers, library, health
from routers.admin import admin_router

# Local imports
from routers import auth, search, papers, library, health
from middleware.logging import setup_logging
from middleware.rate_limit import RateLimitMiddleware
from config import settings
from database.database import init_db

# Setup structured logging
setup_logging()
logger = structlog.get_logger()

# Create custom registry to avoid duplicates
try:
    # Try to get existing metrics first
    REQUEST_COUNT = REGISTRY._names_to_collectors.get('http_requests_total')
    REQUEST_DURATION = REGISTRY._names_to_collectors.get('http_request_duration_seconds')
    FITNESS_VIOLATIONS = REGISTRY._names_to_collectors.get('fitness_function_violations_total')
except:
    REQUEST_COUNT = None
    REQUEST_DURATION = None
    FITNESS_VIOLATIONS = None

# Create metrics only if they don't exist
if REQUEST_COUNT is None:
    REQUEST_COUNT = Counter(
        'http_requests_total', 
        'Total HTTP requests', 
        ['method', 'endpoint', 'status']
    )

if REQUEST_DURATION is None:
    REQUEST_DURATION = Histogram(
        'http_request_duration_seconds', 
        'HTTP request duration', 
        ['method', 'endpoint']
    )

if FITNESS_VIOLATIONS is None:
    FITNESS_VIOLATIONS = Counter(
        'fitness_function_violations_total', 
        'Fitness function violations', 
        ['function', 'endpoint']
    )

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifecycle management"""
    # Startup
    logger.info("🚀 Paperly API Gateway starting up")
    logger.info("🗄️ Initializing SQLite database...")
    
    try:
        await init_db()
        logger.info("✅ Database initialized successfully")
    except Exception as e:
        logger.error("❌ Database initialization failed", error=str(e))
        raise
    
    logger.info("🌟 API Gateway ready to serve requests")
    yield
    
    # Shutdown
    logger.info("🛑 Paperly API Gateway shutting down")

# Create FastAPI application
app = FastAPI(
    title="Paperly API Gateway",
    description="Academic Papers Navigation Platform - POC with SQLite",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    lifespan=lifespan
)

# Security middleware
app.add_middleware(
    TrustedHostMiddleware, 
    allowed_hosts=["*"]  # Configure properly for production
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000", 
        "http://localhost:5173",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:5173"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Rate limiting middleware (simplified without Redis dependency)
app.add_middleware(RateLimitMiddleware, calls=100, period=60)

@app.middleware("http")
async def logging_and_metrics_middleware(request: Request, call_next):
    """
    Comprehensive logging and metrics middleware with fitness functions
    """
    start_time = time.time()
    request_id = str(uuid.uuid4())
    
    # Add request ID to request state
    request.state.request_id = request_id
    
    # Log request start
    logger.info(
        "🔄 Request started",
        method=request.method,
        url=str(request.url),
        request_id=request_id,
        user_agent=request.headers.get("user-agent", "unknown"),
        ip=request.client.host if request.client else "unknown"
    )
    
    try:
        # Process request
        response = await call_next(request)
        duration = time.time() - start_time
        duration_ms = duration * 1000
        
        # Record Prometheus metrics (with error handling)
        try:
            endpoint = request.url.path
            REQUEST_COUNT.labels(
                method=request.method,
                endpoint=endpoint,
                status=response.status_code
            ).inc()
            
            REQUEST_DURATION.labels(
                method=request.method,
                endpoint=endpoint
            ).observe(duration)
        except Exception as e:
            logger.warning("Metrics recording failed", error=str(e))
        
        # Fitness Functions Monitoring
        fitness_checks_passed = True
        
        # 🎯 FITNESS FUNCTION 1: Search requests < 200ms
        if "/search" in endpoint and duration_ms > 200:
            try:
                FITNESS_VIOLATIONS.labels(
                    function="search_response_time",
                    endpoint=endpoint
                ).inc()
            except:
                pass
            logger.warning(
                "⚠️ [FITNESS] Search exceeded 200ms threshold",
                duration_ms=round(duration_ms, 2),
                threshold=200,
                endpoint=endpoint,
                request_id=request_id,
                status="VIOLATION"
            )
            fitness_checks_passed = False
        
        # 🎯 FITNESS FUNCTION 2: Paper catalog rendering < 100ms
        if "/papers/" in endpoint and request.method == "GET" and duration_ms > 100:
            try:
                FITNESS_VIOLATIONS.labels(
                    function="catalog_response_time",
                    endpoint=endpoint
                ).inc()
            except:
                pass
            logger.warning(
                "⚠️ [FITNESS] Catalog rendering exceeded 100ms threshold",
                duration_ms=round(duration_ms, 2),
                threshold=100,
                endpoint=endpoint,
                request_id=request_id,
                status="VIOLATION"
            )
            fitness_checks_passed = False
        
        # 🎯 FITNESS FUNCTION 3: Gateway general performance < 1000ms
        if duration_ms > 1000:
            try:
                FITNESS_VIOLATIONS.labels(
                    function="gateway_response_time",
                    endpoint=endpoint
                ).inc()
            except:
                pass
            logger.warning(
                "⚠️ [FITNESS] Gateway slow response",
                duration_ms=round(duration_ms, 2),
                threshold=1000,
                endpoint=endpoint,
                request_id=request_id,
                status="VIOLATION"
            )
            fitness_checks_passed = False
        
        # Success log with fitness status
        logger.info(
            "✅ Request completed",
            method=request.method,
            url=str(request.url),
            status_code=response.status_code,
            duration_ms=round(duration_ms, 2),
            request_id=request_id,
            fitness_checks_passed=fitness_checks_passed
        )
        
        # Add custom headers
        response.headers["X-Request-ID"] = request_id
        response.headers["X-Response-Time"] = f"{duration_ms:.2f}ms"
        response.headers["X-Fitness-Status"] = "PASS" if fitness_checks_passed else "VIOLATION"
        
        return response
        
    except Exception as e:
        duration = time.time() - start_time
        duration_ms = duration * 1000
        
        logger.error(
            "❌ Request failed",
            method=request.method,
            url=str(request.url),
            error=str(e),
            error_type=type(e).__name__,
            duration_ms=round(duration_ms, 2),
            request_id=request_id
        )
        raise

# Include all routers
app.include_router(
    auth.router, 
    prefix="/api/v1/auth", 
    tags=["Authentication"]
)

app.include_router(
    search.router, 
    prefix="/api/v1/search", 
    tags=["Search"]
)
app.include_router(
    admin_router,
    prefix="/api/v1/admin", 
    tags=["Administration"]
)

app.include_router(
    papers.router, 
    prefix="/api/v1/papers", 
    tags=["Papers"]
)

app.include_router(
    library.router, 
    prefix="/api/v1/library", 
    tags=["Library"]
)

app.include_router(
    health.router, 
    prefix="/api/v1/health", 
    tags=["Health & Monitoring"]
)

@app.get("/metrics")
async def prometheus_metrics():
    """
    Prometheus metrics endpoint for external monitoring
    """
    return Response(
        generate_latest(), 
        media_type=CONTENT_TYPE_LATEST
    )

@app.get("/")
async def root():
    """
    Root endpoint with API information
    """
    return {
        "service": "Paperly API Gateway",
        "version": "1.0.0",
        "description": "Academic Papers Navigation Platform - POC",
        "database": "SQLite (paperly.db)",
        "fitness_functions": [
            "Search response time < 200ms",
            "Catalog rendering < 100ms", 
            "Gateway response < 1000ms",
            "Rate limiting: 100 req/min"
        ],
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
        "sample_papers": 4,
        "timestamp": time.time()
    }

@app.get("/api/v1/status")
async def api_status():
    """
    Detailed API status with fitness functions summary
    """
    try:
        # Get database status
        from database.database import AsyncSessionLocal
        from sqlalchemy import text
        
        db_status = "up"
        paper_count = 0
        user_count = 0
        
        try:
            async with AsyncSessionLocal() as session:
                # Test database connection
                await session.execute(text("SELECT 1"))
                
                # Get counts
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
                "type": "SQLite",
                "file": "paperly.db",
                "papers_count": paper_count,
                "users_count": user_count
            },
            "fitness_functions": {
                "search_latency": {
                    "threshold": "< 200ms",
                    "status": "monitored"
                },
                "catalog_rendering": {
                    "threshold": "< 100ms", 
                    "status": "monitored"
                },
                "gateway_performance": {
                    "threshold": "< 1000ms",
                    "status": "monitored"
                },
                "rate_limiting": {
                    "limit": "100 req/min",
                    "status": "active"
                }
            },
            "features": {
                "authentication": "enabled",
                "paper_search": "enabled",
                "personal_library": "enabled",
                "citations_graph": "simulated",
                "recommendations": "enabled",
                "export_formats": ["bibtex", "apa", "chicago", "ieee"]
            },
            "monitoring": {
                "structured_logging": "enabled",
                "prometheus_metrics": "enabled",
                "request_tracing": "enabled"
            }
        }
        
    except Exception as e:
        logger.error("Status check failed", error=str(e))
        raise HTTPException(status_code=500, detail="Status check failed")

# Custom exception handlers
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Custom HTTP exception handler with logging"""
    logger.warning(
        "HTTP Exception occurred",
        status_code=exc.status_code,
        detail=exc.detail,
        url=str(request.url),
        method=request.method,
        request_id=getattr(request.state, 'request_id', 'unknown')
    )
    
    return {
        "error": {
            "code": exc.status_code,
            "message": exc.detail,
            "timestamp": time.time(),
            "request_id": getattr(request.state, 'request_id', 'unknown')
        }
    }

@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """General exception handler for unexpected errors"""
    logger.error(
        "Unexpected error occurred",
        error=str(exc),
        error_type=type(exc).__name__,
        url=str(request.url),
        method=request.method,
        request_id=getattr(request.state, 'request_id', 'unknown')
    )
    
    return {
        "error": {
            "code": 500,
            "message": "Internal server error",
            "timestamp": time.time(),
            "request_id": getattr(request.state, 'request_id', 'unknown')
        }
    }

if __name__ == "__main__":
    print("🚀 Starting Paperly API Gateway...")
    print("📚 Academic Papers Navigation Platform")
    print("🗄️ Database: SQLite (paperly.db)")
    print("🎯 Fitness Functions: Active")
    print("📊 Monitoring: Enabled")
    print("=" * 50)
    
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=3000,
        reload=True,
        log_level="info",
        access_log=True
    )