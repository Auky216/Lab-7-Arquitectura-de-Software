# database/database.py
import os
from sqlalchemy import create_engine, MetaData, Table, Column, Integer, String, Float, Boolean, DateTime, Text
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, declarative_base
from datetime import datetime
import hashlib
import json

# Database URL
DATABASE_URL = "sqlite+aiosqlite:///./paperly.db"

# SQLAlchemy setup
engine = create_async_engine(DATABASE_URL, echo=False)
AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
Base = declarative_base()

# Simple hash function for POC (replace bcrypt)
def simple_hash(password: str) -> str:
    """Simple hash for POC - DON'T use in production"""
    return hashlib.sha256(password.encode()).hexdigest()

# Tables definition
class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    name = Column(String(255), nullable=False)
    role = Column(String(50), nullable=False, default="student")
    hashed_password = Column(String(255), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

class Paper(Base):
    __tablename__ = "papers"
    
    id = Column(String(100), primary_key=True, index=True)
    title = Column(String(500), nullable=False)
    authors = Column(Text)  # JSON string
    abstract = Column(Text)
    year = Column(Integer)
    journal = Column(String(255))
    doi = Column(String(255), unique=True, index=True)
    pdf_url = Column(String(500))
    open_access = Column(Boolean, default=False)
    keywords = Column(Text)  # JSON string
    citation_count = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)

class LibraryItem(Base):
    __tablename__ = "library_items"
    
    id = Column(Integer, primary_key=True, index=True)
    user_email = Column(String(255), nullable=False, index=True)
    paper_id = Column(String(100), nullable=False)
    tags = Column(Text)  # JSON string
    notes = Column(Text)
    saved_at = Column(DateTime, default=datetime.utcnow)

# Database dependency
async def get_db():
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()

# Initialize database
async def init_db():
    """Initialize database with tables and sample data"""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    # Insert sample data
    await insert_sample_data()

async def insert_sample_data():
    """Insert sample users and papers"""
    async with AsyncSessionLocal() as session:
        # Check if users already exist
        from sqlalchemy import text
        result = await session.execute(text("SELECT COUNT(*) FROM users"))
        user_count = result.scalar()
        
        if user_count == 0:
            # Insert sample users
            users_data = [
                {
                    "email": "student@utec.edu.pe",
                    "name": "Student UTEC",
                    "role": "student",
                    "hashed_password": simple_hash("password123")
                },
                {
                    "email": "admin@utec.edu.pe",
                    "name": "Admin UTEC", 
                    "role": "admin",
                    "hashed_password": simple_hash("admin123")
                }
            ]
            
            for user_data in users_data:
                user = User(**user_data)
                session.add(user)
            
            # Insert sample papers
            papers_data = [
                {
                    "id": "10.1038/nature14539",
                    "title": "Human-level control through deep reinforcement learning",
                    "authors": json.dumps(["Volodymyr Mnih", "Koray Kavukcuoglu", "David Silver"]),
                    "abstract": "The theory of reinforcement learning provides a normative account of agent behavior in uncertain environments...",
                    "year": 2015,
                    "journal": "Nature",
                    "doi": "10.1038/nature14539",
                    "open_access": False,
                    "keywords": json.dumps(["reinforcement learning", "deep learning", "AI", "neural networks"]),
                    "citation_count": 15420
                },
                {
                    "id": "arxiv:1706.03762",
                    "title": "Attention Is All You Need",
                    "authors": json.dumps(["Ashish Vaswani", "Noam Shazeer", "Niki Parmar", "Jakob Uszkoreit"]),
                    "abstract": "The dominant sequence transduction models are based on complex recurrent or convolutional neural networks...",
                    "year": 2017,
                    "journal": "arXiv",
                    "doi": "arxiv:1706.03762",
                    "open_access": True,
                    "keywords": json.dumps(["transformer", "attention", "NLP", "neural networks", "machine learning"]),
                    "citation_count": 45670
                },
                {
                    "id": "10.1126/science.1240527",
                    "title": "Playing Atari with Deep Reinforcement Learning",
                    "authors": json.dumps(["Volodymyr Mnih", "Koray Kavukcuoglu", "David Silver"]),
                    "abstract": "We present the first deep learning model to successfully learn control policies directly from high-dimensional sensory input...",
                    "year": 2013,
                    "journal": "Science",
                    "doi": "10.1126/science.1240527",
                    "open_access": True,
                    "keywords": json.dumps(["deep learning", "reinforcement learning", "games", "neural networks"]),
                    "citation_count": 8934
                },
                {
                    "id": "10.1038/s41586-019-1724-z",
                    "title": "Mastering the game of Go with deep neural networks and tree search",
                    "authors": json.dumps(["David Silver", "Aja Huang", "Chris J. Maddison", "Arthur Guez"]),
                    "abstract": "The game of Go has long been viewed as the most challenging of classic games for artificial intelligence...",
                    "year": 2016,
                    "journal": "Nature",
                    "doi": "10.1038/s41586-019-1724-z",
                    "open_access": False,
                    "keywords": json.dumps(["Go", "AlphaGo", "Monte Carlo", "deep learning", "tree search"]),
                    "citation_count": 12890
                }
            ]
            
            for paper_data in papers_data:
                paper = Paper(**paper_data)
                session.add(paper)
            
            await session.commit()
            print("✅ Sample data inserted successfully")
            print(f"   - {len(users_data)} users created")
            print(f"   - {len(papers_data)} papers created")