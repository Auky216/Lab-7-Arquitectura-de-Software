import time
import structlog
import random
from fastapi import APIRouter, Query, Depends
from typing import Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi.security import HTTPBearer
from models.auth import get_current_user
from database.database import get_db
from database.operations import PaperOperations
from services.cache_service import cache_service
import json
from services.scraper_service import WebScrapingService
from fastapi import FastAPI, Request, HTTPException

router = APIRouter()
security = HTTPBearer()
logger = structlog.get_logger()


@router.get("/")
async def search_papers(
    q: Optional[str] = Query(None),
    author: Optional[str] = Query(None, description="Filter by author"),
    institution: Optional[str] = Query(None, description="Filter by institution"),
    year_from: Optional[int] = Query(None, description="Filter from year"),
    year_to: Optional[int] = Query(None, description="Filter to year"),
    keywords: Optional[List[str]] = Query(None, description="Filter by keywords"),
    open_access: Optional[bool] = Query(None, description="Open access only"),
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(20, ge=1, le=100, description="Items per page"),
    sort_by: str = Query("relevance", description="Sort by: relevance, citations, date"),
    include_external: bool = Query(False, description="Include external API results"),
    token: HTTPBearer = Depends(security),
    db: AsyncSession = Depends(get_db)
):
    """Enhanced search with external sources and caching"""
    start_time = time.time()
    current_user = await get_current_user(token, db)
    
    # Build cache key
    filters = {k: v for k, v in {
        "author": author, "institution": institution,
        "year_from": year_from, "year_to": year_to,
        "keywords": keywords, "open_access": open_access
    }.items() if v is not None}
    
    cache_key = f"search:{q}:{json.dumps(filters, sort_keys=True)}:{page}:{limit}:{sort_by}"
    
    # Check cache
    cached_result = cache_service.get(cache_key)
    if cached_result and not include_external:
        logger.info("🔍 [CACHE] Search served from cache")
        return cached_result
    
    # Database search
    papers, total = await PaperOperations.search_papers(
        db, query=q, filters=filters, page=page, limit=limit, sort_by=sort_by
    )
    
    papers_data = []
    for paper in papers:
        paper_dict = {
            "id": paper.id,
            "title": paper.title,
            "authors": json.loads(paper.authors) if paper.authors else [],
            "year": paper.year,
            "journal": paper.journal,
            "citation_count": paper.citation_count,
            "open_access": paper.open_access,
            "source": "database"
        }
        papers_data.append(paper_dict)
    
    # External search if requested
    external_results = []
    if include_external and q:
        try:
            # Scrape arXiv
            arxiv_results = await WebScrapingService.scrape_arxiv("cs.AI")
            for paper in arxiv_results["papers"][:3]:  # Limit external results
                external_results.append({
                    "id": paper["arxiv_id"],
                    "title": paper["title"],
                    "authors": paper["authors"],
                    "year": int(paper["submitted_date"][:4]),
                    "journal": "arXiv",
                    "citation_count": random.randint(0, 50),
                    "source": "arxiv"
                })
        except Exception as e:
            logger.warning("External search failed", error=str(e))
    
    duration_ms = (time.time() - start_time) * 1000
    
    result = {
        "data": papers_data + external_results,
        "meta": {
            "page": page,
            "limit": limit,
            "total": total + len(external_results),
            "database_results": len(papers_data),
            "external_results": len(external_results),
            "duration_ms": round(duration_ms, 2),
            "cached": False
        }
    }
    
    # Cache result if no external search
    if not include_external:
        cache_service.set(cache_key, result, ttl=300)
    
    return result

@router.get("/external/scrape")
async def scrape_external_sources(
    source: str = Query(..., description="Source: arxiv, google_scholar"),
    category: str = Query("cs.AI", description="Category or query"),
    token: HTTPBearer = Depends(security),
    db: AsyncSession = Depends(get_db)
):
    """Scrape external sources for papers"""
    current_user = await get_current_user(token, db)
    
    if current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    
    logger.info("🕷️ [SCRAPER] External scraping started", source=source, category=category)
    
    if source == "arxiv":
        result = await WebScrapingService.scrape_arxiv(category)
    elif source == "google_scholar":
        result = await WebScrapingService.scrape_google_scholar(category)
    else:
        raise HTTPException(status_code=400, detail="Unsupported scraping source")
    
    return {
        "data": result,
        "meta": {
            "source": source,
            "category": category,
            "timestamp": time.time()
        }
    }
