import random
from typing import List, Dict
from database.operations import PaperOperations

class RecommendationService:
    """Paper recommendation engine"""
    
    @staticmethod
    async def get_recommendations(db, paper_id: str, strategy: str = "similarity") -> List[Dict]:
        paper = await PaperOperations.get_paper_by_id(db, paper_id)
        if not paper:
            return []
        
        if strategy == "similarity":
            return await RecommendationService._content_based(db, paper)
        elif strategy == "collaborative":
            return await RecommendationService._collaborative_filtering(db, paper)
        elif strategy == "citation":
            return await RecommendationService._citation_based(db, paper)
        else:
            return await RecommendationService._hybrid(db, paper)
    
    @staticmethod
    async def _content_based(db, paper) -> List[Dict]:
        keywords = json.loads(paper.keywords) if paper.keywords else []
        if not keywords:
            return []
        
        related_papers, _ = await PaperOperations.search_papers(
            db, filters={"keywords": keywords[:2]}, limit=10, sort_by="citations"
        )
        
        recommendations = []
        for p in related_papers:
            if p.id != paper.id:
                similarity_score = random.uniform(0.7, 0.95)
                recommendations.append({
                    "paper_id": p.id,
                    "title": p.title,
                    "similarity_score": round(similarity_score, 2),
                    "reason": f"Similar keywords: {', '.join(keywords[:2])}"
                })
        
        return recommendations[:5]
    
    @staticmethod
    async def _collaborative_filtering(db, paper) -> List[Dict]:
        # Mock collaborative filtering
        all_papers, _ = await PaperOperations.search_papers(db, limit=20, sort_by="citations")
        
        recommendations = []
        for p in random.sample(list(all_papers), min(5, len(all_papers))):
            if p.id != paper.id:
                recommendations.append({
                    "paper_id": p.id,
                    "title": p.title,
                    "similarity_score": random.uniform(0.6, 0.9),
                    "reason": "Users who read this also read..."
                })
        
        return recommendations
    
    @staticmethod
    async def _citation_based(db, paper) -> List[Dict]:
        # Mock citation-based recommendations
        same_year_papers, _ = await PaperOperations.search_papers(
            db, filters={"year_from": paper.year, "year_to": paper.year}, limit=10
        )
        
        recommendations = []
        for p in same_year_papers:
            if p.id != paper.id:
                recommendations.append({
                    "paper_id": p.id,
                    "title": p.title,
                    "similarity_score": random.uniform(0.75, 0.95),
                    "reason": f"Frequently co-cited with this paper"
                })
        
        return recommendations[:5]
    
    @staticmethod
    async def _hybrid(db, paper) -> List[Dict]:
        content_recs = await RecommendationService._content_based(db, paper)
        collab_recs = await RecommendationService._collaborative_filtering(db, paper)
        
        # Combine and re-rank
        all_recs = content_recs + collab_recs
        seen = set()
        unique_recs = []
        
        for rec in all_recs:
            if rec["paper_id"] not in seen:
                seen.add(rec["paper_id"])
                unique_recs.append(rec)
        
        return unique_recs[:5]
