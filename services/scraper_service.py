import random
from typing import List, Dict

class WebScrapingService:
    """Mock web scraping service"""
    
    @staticmethod
    async def scrape_arxiv(category: str = "cs.AI") -> List[Dict]:
        # Mock arXiv scraping
        await asyncio.sleep(1.0)
        
        papers = []
        for i in range(random.randint(5, 15)):
            papers.append({
                "title": f"arXiv Paper {i+1}: Latest in {category}",
                "authors": [f"Researcher {i+1}", f"Co-researcher {i+1}"],
                "abstract": f"This is a mock abstract for paper {i+1} in category {category}...",
                "arxiv_id": f"{random.randint(2020, 2024)}.{random.randint(1000, 9999)}",
                "category": category,
                "submitted_date": f"2024-{random.randint(1, 12):02d}-{random.randint(1, 28):02d}",
                "keywords": [category.split('.')[1], "research", "analysis"]
            })
        
        return {
            "status": "success",
            "papers": papers,
            "category": category,
            "scraped_at": time.time()
        }
    
    @staticmethod
    async def scrape_google_scholar(query: str) -> Dict:
        # Mock Google Scholar scraping
        await asyncio.sleep(1.5)
        
        return {
            "status": "success",
            "query": query,
            "results": [
                {
                    "title": f"Scholar Result: {query} Analysis",
                    "authors": ["Dr. Scholar", "Prof. Research"],
                    "snippet": f"This paper analyzes {query} using advanced methods...",
                    "citations": random.randint(10, 1000),
                    "year": random.randint(2015, 2024),
                    "url": f"https://scholar.google.com/mock/{random.randint(1000, 9999)}"
                }
            ],
            "total_results": random.randint(100, 10000)
        }