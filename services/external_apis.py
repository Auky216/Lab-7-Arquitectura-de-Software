import random
import asyncio
from typing import List, Dict

class ExternalAPIService:
    """Mock external API integrations"""
    
    @staticmethod
    async def fetch_from_crossref(doi: str) -> Dict:
        # Mock CrossRef API response
        await asyncio.sleep(0.5)  # Simulate API delay
        
        return {
            "status": "success",
            "data": {
                "title": f"Paper from CrossRef API - {doi}",
                "authors": ["Dr. Mock Author", "Prof. Example"],
                "journal": "Mock Journal of Science",
                "year": random.randint(2015, 2024),
                "abstract": "This is a mock abstract fetched from CrossRef API...",
                "keywords": ["machine learning", "artificial intelligence"],
                "citation_count": random.randint(10, 1000),
                "doi": doi,
                "open_access": random.choice([True, False])
            },
            "source": "crossref"
        }
    
    @staticmethod
    async def fetch_from_ieee(query: str) -> List[Dict]:
        # Mock IEEE API response
        await asyncio.sleep(0.7)
        
        papers = []
        for i in range(random.randint(3, 8)):
            papers.append({
                "title": f"IEEE Paper {i+1}: {query}",
                "authors": [f"IEEE Author {i+1}", f"Co-author {i+1}"],
                "journal": "IEEE Transactions on Mock",
                "year": random.randint(2018, 2024),
                "doi": f"10.1109/MOCK{random.randint(1000, 9999)}.{random.randint(2018, 2024)}",
                "citation_count": random.randint(5, 500)
            })
        
        return {
            "status": "success",
            "data": papers,
            "total": len(papers),
            "source": "ieee"
        }
    
    @staticmethod
    async def fetch_from_semantic_scholar(author: str) -> Dict:
        # Mock Semantic Scholar API
        await asyncio.sleep(0.3)
        
        return {
            "status": "success",
            "data": {
                "author_id": f"mock_id_{random.randint(1000, 9999)}",
                "name": author,
                "h_index": random.randint(10, 100),
                "citation_count": random.randint(100, 10000),
                "papers": [
                    {
                        "title": f"Paper by {author} - Study 1",
                        "year": random.randint(2015, 2024),
                        "citations": random.randint(10, 500)
                    }
                ]
            },
            "source": "semantic_scholar"
        }
