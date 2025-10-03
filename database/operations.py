from sqlalchemy import select, and_, or_, func
from sqlalchemy.ext.asyncio import AsyncSession
from database.database import User, Paper, LibraryItem
import json

class UserOperations:
    @staticmethod
    async def get_user_by_email(db: AsyncSession, email: str):
        result = await db.execute(select(User).where(User.email == email))
        return result.scalar_one_or_none()

class PaperOperations:
    @staticmethod
    async def search_papers(db: AsyncSession, query: str = None, filters: dict = None, 
                          page: int = 1, limit: int = 20, sort_by: str = "relevance"):
        """Search papers with filters"""
        stmt = select(Paper)
        
        # Text search
        if query:
            stmt = stmt.where(
                or_(
                    Paper.title.contains(query),
                    Paper.abstract.contains(query),
                    Paper.keywords.contains(query)
                )
            )
        
        # Apply filters
        if filters:
            if filters.get("author"):
                stmt = stmt.where(Paper.authors.contains(filters["author"]))
            if filters.get("year_from"):
                stmt = stmt.where(Paper.year >= filters["year_from"])
            if filters.get("year_to"):
                stmt = stmt.where(Paper.year <= filters["year_to"])
            if filters.get("open_access") is not None:
                stmt = stmt.where(Paper.open_access == filters["open_access"])
            if filters.get("keywords"):
                for keyword in filters["keywords"]:
                    stmt = stmt.where(Paper.keywords.contains(keyword))
        
        # Sorting
        if sort_by == "citations":
            stmt = stmt.order_by(Paper.citation_count.desc())
        elif sort_by == "date":
            stmt = stmt.order_by(Paper.year.desc())
        else:  # relevance (default)
            stmt = stmt.order_by(Paper.citation_count.desc())
        
        # Pagination
        offset = (page - 1) * limit
        stmt = stmt.offset(offset).limit(limit)
        
        result = await db.execute(stmt)
        papers = result.scalars().all()
        
        # Count total
        count_stmt = select(func.count(Paper.id))
        if query:
            count_stmt = count_stmt.where(
                or_(
                    Paper.title.contains(query),
                    Paper.abstract.contains(query),
                    Paper.keywords.contains(query)
                )
            )
        total_result = await db.execute(count_stmt)
        total = total_result.scalar()
        
        return papers, total
    
    @staticmethod
    async def get_paper_by_id(db: AsyncSession, paper_id: str):
        result = await db.execute(select(Paper).where(Paper.id == paper_id))
        return result.scalar_one_or_none()

class LibraryOperations:
    @staticmethod
    async def get_user_library(db: AsyncSession, user_email: str):
        result = await db.execute(
            select(LibraryItem)
            .where(LibraryItem.user_email == user_email)
            .order_by(LibraryItem.saved_at.desc())
        )
        return result.scalars().all()
    
    @staticmethod
    async def save_paper_to_library(db: AsyncSession, user_email: str, paper_id: str, 
                                  tags: list = None, notes: str = None):
        # Check if already exists
        result = await db.execute(
            select(LibraryItem)
            .where(and_(LibraryItem.user_email == user_email, LibraryItem.paper_id == paper_id))
        )
        existing = result.scalar_one_or_none()
        
        if existing:
            # Update existing
            existing.tags = json.dumps(tags or [])
            existing.notes = notes or ""
            await db.commit()
            return existing
        else:
            # Create new
            library_item = LibraryItem(
                user_email=user_email,
                paper_id=paper_id,
                tags=json.dumps(tags or []),
                notes=notes or ""
            )
            db.add(library_item)
            await db.commit()
            await db.refresh(library_item)
            return library_item
    
    @staticmethod
    async def remove_paper_from_library(db: AsyncSession, user_email: str, paper_id: str):
        result = await db.execute(
            select(LibraryItem)
            .where(and_(LibraryItem.user_email == user_email, LibraryItem.paper_id == paper_id))
        )
        library_item = result.scalar_one_or_none()
        
        if library_item:
            await db.delete(library_item)
            await db.commit()
            return True
        return False
