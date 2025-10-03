# middleware/rate_limit.py
import time
from fastapi import HTTPException, Request
from starlette.middleware.base import BaseHTTPMiddleware

class RateLimitMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, calls: int = 100, period: int = 60):
        super().__init__(app)
        self.calls = calls
        self.period = period
        self.memory_store = {}

    async def dispatch(self, request: Request, call_next):
        client_ip = request.client.host if request.client else "unknown"
        current_time = int(time.time())
        key = f"rate_limit:{client_ip}:{current_time // self.period}"
        
        if key not in self.memory_store:
            self.memory_store[key] = 0
        
        self.memory_store[key] += 1
        
        # Clean old keys
        for k in list(self.memory_store.keys()):
            if int(k.split(":")[-1]) < current_time // self.period - 1:
                del self.memory_store[k]
        
        if self.memory_store[key] > self.calls:
            raise HTTPException(
                status_code=429,
                detail="Rate limit exceeded"
            )
        
        response = await call_next(request)
        return response

class AdvancedRateLimitMiddleware(BaseHTTPMiddleware):
    """Advanced rate limiting with different tiers"""
    
    def __init__(self, app):
        super().__init__(app)
        self.limits = {
            "anonymous": {"calls": 50, "period": 60},
            "student": {"calls": 200, "period": 60},
            "admin": {"calls": 1000, "period": 60}
        }
        self.memory_store = {}
    
    async def dispatch(self, request: Request, call_next):
        # Determine user tier
        user_tier = "anonymous"
        auth_header = request.headers.get("authorization")
        
        if auth_header:
            user_tier = "student"  # Default for authenticated users
            if "admin" in auth_header:  # Simple check for demo
                user_tier = "admin"
        
        # Apply rate limiting based on tier
        client_ip = request.client.host if request.client else "unknown"
        current_time = int(time.time())
        
        limits = self.limits[user_tier]
        key = f"rate_limit:{client_ip}:{user_tier}:{current_time // limits['period']}"
        
        if key not in self.memory_store:
            self.memory_store[key] = 0
        
        self.memory_store[key] += 1
        
        # Clean old keys
        for k in list(self.memory_store.keys()):
            if int(k.split(":")[-1]) < current_time // limits['period'] - 1:
                del self.memory_store[k]
        
        if self.memory_store[key] > limits["calls"]:
            raise HTTPException(
                status_code=429,
                detail=f"Rate limit exceeded for {user_tier} tier. Limit: {limits['calls']}/{limits['period']}s"
            )
        
        response = await call_next(request)
        
        # Add rate limit headers
        response.headers["X-RateLimit-Limit"] = str(limits["calls"])
        response.headers["X-RateLimit-Remaining"] = str(max(0, limits["calls"] - self.memory_store[key]))
        response.headers["X-RateLimit-Reset"] = str((current_time // limits['period'] + 1) * limits['period'])
        response.headers["X-RateLimit-Tier"] = user_tier
        
        return response