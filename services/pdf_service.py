import random
import asyncio
from typing import Dict, List

class PDFProcessingService:
    """Mock PDF processing service"""
    
    @staticmethod
    async def extract_metadata(pdf_content: bytes) -> Dict:
        # Mock PDF metadata extraction
        await asyncio.sleep(2.0)  # Simulate processing time
        
        return {
            "status": "success",
            "metadata": {
                "title": "Extracted Title from PDF",
                "authors": ["Extracted Author 1", "Extracted Author 2"],
                "abstract": "This abstract was extracted from the PDF using OCR and NLP techniques...",
                "keywords": ["extracted", "PDF", "processing", "NLP"],
                "pages": random.randint(8, 25),
                "file_size": f"{random.randint(500, 5000)}KB",
                "language": "en",
                "creation_date": "2024-01-15",
                "doi": f"10.extracted/{random.randint(1000, 9999)}"
            },
            "references": [
                {"title": "Reference 1", "authors": ["Ref Author 1"]},
                {"title": "Reference 2", "authors": ["Ref Author 2"]}
            ],
            "processing_time": 2.0
        }
    
    @staticmethod
    async def extract_citations(pdf_content: bytes) -> List[Dict]:
        # Mock citation extraction
        await asyncio.sleep(1.5)
        
        return [
            {
                "reference_number": i+1,
                "title": f"Citation {i+1} extracted from PDF",
                "authors": [f"Cited Author {i+1}"],
                "year": random.randint(2010, 2023),
                "confidence": round(random.uniform(0.7, 0.95), 2)
            }
            for i in range(random.randint(10, 30))
        ]
