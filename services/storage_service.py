import random
from typing import Dict

class DistributedStorageService:
    """Mock distributed file storage (CDN simulation)"""
    
    def __init__(self):
        self.regions = ["us-east", "eu-west", "asia-pacific", "latam"]
        self.storage_stats = {
            "total_files": random.randint(10000, 50000),
            "total_size": f"{random.randint(500, 2000)}GB",
            "regions": len(self.regions)
        }
    
    async def upload_file(self, file_content: bytes, filename: str) -> Dict:
        # Mock file upload to distributed storage
        await asyncio.sleep(0.5)
        
        file_id = f"file_{random.randint(100000, 999999)}"
        
        return {
            "status": "success",
            "file_id": file_id,
            "filename": filename,
            "size": len(file_content),
            "regions": random.sample(self.regions, random.randint(2, 4)),
            "cdn_urls": {
                region: f"https://cdn-{region}.paperly.com/{file_id}/{filename}"
                for region in self.regions
            },
            "upload_time": time.time()
        }
    
    def get_optimal_url(self, file_id: str, user_region: str = "latam") -> str:
        # Return closest CDN URL
        closest_region = "latam" if user_region == "latam" else "us-east"
        return f"https://cdn-{closest_region}.paperly.com/{file_id}"
    
    def get_storage_stats(self) -> Dict:
        return self.storage_stats

storage_service = DistributedStorageService()