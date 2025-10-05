# database/database.py
import os
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base
from datetime import datetime
import hashlib
import json

# PostgreSQL Configuration
POSTGRES_USER = os.getenv("POSTGRES_USER", "postgres")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD", "2099")
POSTGRES_DB = os.getenv("POSTGRES_DB", "paperly_db")
POSTGRES_HOST = os.getenv("POSTGRES_HOST", "localhost")
POSTGRES_PORT = os.getenv("POSTGRES_PORT", "5432")

# PostgreSQL URL
DATABASE_URL = f"postgresql+asyncpg://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}"

# Engine optimizado para alta concurrencia
engine = create_async_engine(
    DATABASE_URL,
    echo=False,
    pool_size=20,              # Reducido para múltiples workers
    max_overflow=40,           # 20 + 40 = 60 max por worker
    pool_timeout=30,           # Timeout más corto
    pool_pre_ping=True,
    pool_recycle=1800,         # Reciclar cada 30 min
    connect_args={
        "command_timeout": 10,
        "server_settings": {
            "jit": "off",
            "statement_timeout": "30000"  # 10 segundos max por query
        }
    }
)

# Session maker
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False
)

Base = declarative_base()

def simple_hash(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()

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
    authors = Column(Text)
    abstract = Column(Text)
    year = Column(Integer)
    journal = Column(String(255))
    doi = Column(String(255), unique=True, index=True)
    pdf_url = Column(String(500))
    open_access = Column(Boolean, default=False)
    keywords = Column(Text)
    citation_count = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)

class LibraryItem(Base):
    __tablename__ = "library_items"
    
    id = Column(Integer, primary_key=True, index=True)
    user_email = Column(String(255), nullable=False, index=True)
    paper_id = Column(String(100), nullable=False)
    tags = Column(Text)
    notes = Column(Text)
    saved_at = Column(DateTime, default=datetime.utcnow)

async def get_db():
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()

async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    await insert_sample_data()

async def insert_sample_data():
    async with AsyncSessionLocal() as session:
        from sqlalchemy import text
        result = await session.execute(text("SELECT COUNT(*) FROM users"))
        user_count = result.scalar()
        
        if user_count == 0:
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