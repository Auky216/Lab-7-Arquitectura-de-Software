import time
import json
import asyncio
from fastapi import APIRouter, Path, Query, Depends, HTTPException, Body, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi.security import HTTPBearer
from models.auth import get_current_user
from database.database import get_db
from database.operations import PaperOperations
from services.cache_service import cache_service
from services.recommendation_service import RecommendationService
from services.citation_service import CitationGraphService
from services.quality_service import QualityControlService
from services.external_apis import ExternalAPIService
from services.pdf_service import PDFProcessingService
from services.storage_service import storage_service
import structlog

router = APIRouter()
security = HTTPBearer()
logger = structlog.get_logger()

@router.get("/{paper_id}")
async def get_paper(
    paper_id: str = Path(..., description="Paper ID or DOI"),
    token: HTTPBearer = Depends(security),
    db: AsyncSession = Depends(get_db)
):
    """Get paper details with caching"""
    start_time = time.time()
    current_user = await get_current_user(token, db)
    
    # Check cache first
    cache_key = f"paper:{paper_id}"
    cached_paper = cache_service.get(cache_key)
    
    if cached_paper:
        logger.info("📦 [CACHE] Paper served from cache", paper_id=paper_id)
        return cached_paper
    
    paper = await PaperOperations.get_paper_by_id(db, paper_id)
    
    if not paper:
        raise HTTPException(status_code=404, detail="Paper not found")
    
    paper_data = {
        "id": paper.id,
        "title": paper.title,
        "authors": json.loads(paper.authors) if paper.authors else [],
        "abstract": paper.abstract,
        "year": paper.year,
        "journal": paper.journal,
        "doi": paper.doi,
        "keywords": json.loads(paper.keywords) if paper.keywords else [],
        "citation_count": paper.citation_count,
        "open_access": paper.open_access
    }
    
    result = {
        "data": paper_data,
        "meta": {
            "cached": False,
            "duration_ms": round((time.time() - start_time) * 1000, 2)
        }
    }
    
    # Cache the result
    cache_service.set(cache_key, result, ttl=300)
    
    return result

@router.get("/{paper_id}/recommendations")
async def get_recommendations(
    paper_id: str = Path(..., description="Paper ID"),
    strategy: str = Query("similarity", description="Recommendation strategy"),
    limit: int = Query(5, ge=1, le=20),
    token: HTTPBearer = Depends(security),
    db: AsyncSession = Depends(get_db)
):
    """Get paper recommendations"""
    current_user = await get_current_user(token, db)
    
    cache_key = f"recommendations:{paper_id}:{strategy}:{limit}"
    cached_recs = cache_service.get(cache_key)
    
    if cached_recs:
        logger.info("🎯 [CACHE] Recommendations served from cache")
        return cached_recs
    
    recommendations = await RecommendationService.get_recommendations(
        db, paper_id, strategy
    )
    
    result = {
        "data": recommendations[:limit],
        "meta": {
            "strategy": strategy,
            "total": len(recommendations),
            "paper_id": paper_id
        }
    }
    
    cache_service.set(cache_key, result, ttl=600)
    return result

@router.get("/{paper_id}/citation-graph")
async def get_citation_graph(
    paper_id: str = Path(..., description="Paper ID"),
    token: HTTPBearer = Depends(security),
    db: AsyncSession = Depends(get_db)
):
    """Get citation graph for paper"""
    current_user = await get_current_user(token, db)
    
    graph_data = await CitationGraphService.get_citation_graph(db, paper_id)
    metrics = CitationGraphService.calculate_paper_metrics(graph_data)
    
    return {
        "data": {
            "graph": graph_data,
            "metrics": metrics
        },
        "meta": {
            "paper_id": paper_id,
            "generated_at": time.time()
        }
    }

@router.post("/upload")
async def upload_paper(
    file: UploadFile = File(...),
    token: HTTPBearer = Depends(security),
    db: AsyncSession = Depends(get_db)
):
    """Upload and process a paper PDF"""
    current_user = await get_current_user(token, db)
    
    if not file.filename.endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Only PDF files are allowed")
    
    logger.info("📤 [UPLOAD] Processing PDF upload", filename=file.filename)
    
    # Read file content
    content = await file.read()
    
    # Process PDF (mock)
    pdf_metadata = await PDFProcessingService.extract_metadata(content)
    citations = await PDFProcessingService.extract_citations(content)
    
    # Quality control
    quality_check = QualityControlService.validate_paper_metadata(pdf_metadata["metadata"])
    duplicate_check = QualityControlService.check_duplicate(db, pdf_metadata["metadata"])
    
    # Store in distributed storage (mock)
    storage_result = await storage_service.upload_file(content, file.filename)
    
    return {
        "data": {
            "upload_status": "success",
            "file_info": {
                "filename": file.filename,
                "size": len(content),
                "file_id": storage_result["file_id"]
            },
            "extracted_metadata": pdf_metadata["metadata"],
            "citations_found": len(citations),
            "quality_score": quality_check["score"],
            "quality_status": quality_check["status"],
            "duplicate_check": duplicate_check,
            "storage": storage_result
        },
        "meta": {
            "processing_time": pdf_metadata["processing_time"],
            "next_steps": [
                "Review quality issues" if quality_check["issues"] else "Ready for indexing",
                "Manual review required" if duplicate_check["is_duplicate"] else "No duplicates found"
            ]
        }
    }

@router.post("/ingest/external")
async def ingest_from_external(
    source: str = Body(..., description="Source: crossref, ieee, semantic_scholar"),
    query: str = Body(..., description="Search query or identifier"),
    token: HTTPBearer = Depends(security),
    db: AsyncSession = Depends(get_db)
):
    """Ingest papers from external APIs"""
    current_user = await get_current_user(token, db)
    
    if current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    
    logger.info("🔗 [INGEST] External API ingestion started", source=source, query=query)
    
    start_time = time.time()
    
    if source == "crossref":
        result = await ExternalAPIService.fetch_from_crossref(query)
    elif source == "ieee":
        result = await ExternalAPIService.fetch_from_ieee(query)
    elif source == "semantic_scholar":
        result = await ExternalAPIService.fetch_from_semantic_scholar(query)
    else:
        raise HTTPException(status_code=400, detail="Unsupported source")
    
    processing_time = time.time() - start_time
    
    return {
        "data": result,
        "meta": {
            "source": source,
            "query": query,
            "processing_time": round(processing_time, 2),
            "timestamp": time.time()
        }
    }

@router.get("/{paper_id}/export")
async def export_paper(
    paper_id: str = Path(..., description="Paper ID"),
    format: str = Query("bibtex", description="Export format"),
    token: HTTPBearer = Depends(security),
    db: AsyncSession = Depends(get_db)
):
    """Export paper in various formats"""
    current_user = await get_current_user(token, db)
    
    paper = await PaperOperations.get_paper_by_id(db, paper_id)
    if not paper:
        raise HTTPException(status_code=404, detail="Paper not found")
    
    authors = json.loads(paper.authors) if paper.authors else []
    authors_str = ", ".join(authors)
    
    formats = {
        "bibtex": f"""@article{{{paper.id.replace('/', '_').replace(':', '_')},
  title={{{paper.title}}},
  author={{{authors_str}}},
  journal={{{paper.journal or 'Unknown'}}},
  year={{{paper.year or 'Unknown'}}},
  doi={{{paper.doi or 'Unknown'}}}
}}""",
        "apa": f"{authors_str} ({paper.year or 'n.d.'}). {paper.title}. {paper.journal or 'Unknown Journal'}.",
        "chicago": f"{authors_str}. \"{paper.title}.\" {paper.journal or 'Unknown Journal'} {paper.year or 'n.d.'}.",
        "ieee": f"{authors_str}, \"{paper.title},\" {paper.journal or 'Unknown Journal'}, {paper.year or 'n.d.'}.",
        "mla": f"{authors_str}. \"{paper.title}.\" {paper.journal or 'Unknown Journal'}, {paper.year or 'n.d.'}.",
        "harvard": f"{authors_str} {paper.year or 'n.d.'}, '{paper.title}', {paper.journal or 'Unknown Journal'}."
    }
    
    if format not in formats:
        raise HTTPException(status_code=400, detail=f"Unsupported format. Available: {list(formats.keys())}")
    
    return {
        "data": {
            "citation": formats[format],
            "format": format,
            "paper_id": paper_id
        },
        "meta": {
            "available_formats": list(formats.keys()),
            "generated_at": time.time()
        }
    }
