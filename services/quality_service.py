from typing import Dict
import random

class QualityControlService:
    """Quality control and validation"""
    
    @staticmethod
    def validate_paper_metadata(paper_data: Dict) -> Dict:
        issues = []
        score = 100
        
        # Title validation
        if not paper_data.get("title") or len(paper_data["title"]) < 10:
            issues.append("Title too short or missing")
            score -= 20
        
        # Authors validation
        authors = paper_data.get("authors", [])
        if not authors or len(authors) == 0:
            issues.append("No authors specified")
            score -= 25
        
        # Year validation
        year = paper_data.get("year")
        if not year or year < 1900 or year > 2025:
            issues.append("Invalid publication year")
            score -= 15
        
        # DOI validation (mock)
        doi = paper_data.get("doi")
        if doi and not (doi.startswith("10.") or doi.startswith("arxiv:")):
            issues.append("Invalid DOI format")
            score -= 10
        
        # Abstract validation
        abstract = paper_data.get("abstract")
        if not abstract or len(abstract) < 50:
            issues.append("Abstract too short or missing")
            score -= 15
        
        # Keywords validation
        keywords = paper_data.get("keywords", [])
        if len(keywords) < 2:
            issues.append("Insufficient keywords")
            score -= 10
        
        status = "approved" if score >= 80 else "needs_review" if score >= 60 else "rejected"
        
        return {
            "score": max(0, score),
            "status": status,
            "issues": issues,
            "recommendations": [
                "Add more descriptive keywords",
                "Verify author affiliations",
                "Check abstract completeness"
            ] if issues else []
        }
    
    @staticmethod
    def check_duplicate(db, paper_data: Dict) -> Dict:
        # Mock duplicate detection
        similarity_threshold = 0.85
        potential_duplicates = []
        
        # Simulate duplicate checking
        if random.random() < 0.1:  # 10% chance of duplicate
            potential_duplicates.append({
                "paper_id": "mock_duplicate_id",
                "title": "Similar title found",
                "similarity": round(random.uniform(0.85, 0.95), 2),
                "match_type": "title_similarity"
            })
        
        return {
            "is_duplicate": len(potential_duplicates) > 0,
            "confidence": random.uniform(0.7, 0.95),
            "potential_duplicates": potential_duplicates
        }
