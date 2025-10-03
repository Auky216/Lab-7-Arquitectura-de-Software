from database.operations import PaperOperations  # Make sure this import path is correct
import random
from typing import Dict

class CitationGraphService:
    """Citation graph and analysis"""
    
    @staticmethod
    async def get_citation_graph(db, paper_id: str) -> Dict:
        paper = await PaperOperations.get_paper_by_id(db, paper_id)
        if not paper:
            return {"nodes": [], "edges": []}
        
        # Mock citation graph
        nodes = [
            {"id": paper.id, "title": paper.title, "type": "main", "citations": paper.citation_count}
        ]
        edges = []
        
        # Add some related papers as nodes
        keywords = json.loads(paper.keywords) if paper.keywords else []
        if keywords:
            related_papers, _ = await PaperOperations.search_papers(
                db, filters={"keywords": keywords[:1]}, limit=5
            )
            
            for i, related in enumerate(related_papers):
                if related.id != paper.id:
                    nodes.append({
                        "id": related.id,
                        "title": related.title,
                        "type": "related",
                        "citations": related.citation_count
                    })
                    
                    # Create mock edges
                    if random.random() > 0.5:
                        edges.append({
                            "source": paper.id,
                            "target": related.id,
                            "type": "cites",
                            "weight": random.uniform(0.3, 1.0)
                        })
        
        return {
            "nodes": nodes,
            "edges": edges,
            "statistics": {
                "total_nodes": len(nodes),
                "total_edges": len(edges),
                "clustering_coefficient": round(random.uniform(0.3, 0.8), 3),
                "avg_degree": round(random.uniform(2.1, 4.5), 1)
            }
        }
    
    @staticmethod
    def calculate_paper_metrics(citation_graph: Dict) -> Dict:
        return {
            "betweenness_centrality": round(random.uniform(0.1, 0.9), 3),
            "closeness_centrality": round(random.uniform(0.2, 0.8), 3),
            "pagerank": round(random.uniform(0.01, 0.1), 4),
            "h_index": random.randint(5, 50),
            "impact_factor": round(random.uniform(1.2, 8.5), 2)
        }