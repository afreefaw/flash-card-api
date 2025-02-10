import os
import json
import logging
from datetime import datetime
from typing import Optional, List, Dict, Any
from sqlalchemy import create_engine, Column, Integer, String, DateTime, text, JSON
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import SQLAlchemyError

# Set up logging
logger = logging.getLogger('documents')
logger.setLevel(logging.INFO)
file_handler = logging.FileHandler('documents.log')
file_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
logger.addHandler(file_handler)

# Database setup
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///documents.db")
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class Document(Base):
    __tablename__ = 'documents'
    
    id = Column(Integer, primary_key=True)
    title = Column(String, unique=True, nullable=False)
    # Use JSON for SQLite, JSONB for PostgreSQL
    tags = Column(JSON().with_variant(JSONB, 'postgresql'), nullable=False, default=list)
    content = Column(String, nullable=False)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

# Create tables
Base.metadata.create_all(bind=engine)

class DocumentDB:
    def __init__(self, db_url=None):
        """Initialize database connection"""
        if db_url:
            self.engine = create_engine(db_url)
            self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
            self.is_sqlite = db_url.startswith('sqlite')
        else:
            self.engine = engine
            self.SessionLocal = SessionLocal
            self.is_sqlite = DATABASE_URL.startswith('sqlite')
        logger.info(f"Initialized DocumentDB with {db_url or DATABASE_URL} (Using {'SQLite' if self.is_sqlite else 'PostgreSQL'})")
    
    def _get_db(self):
        db = self.SessionLocal()
        try:
            return db
        except:
            db.close()
            raise

    def create_document(self, title: str, content: str, tags: List[str]) -> int:
        """Create a new document"""
        db = self._get_db()
        try:
            document = Document(
                title=title,
                content=content,
                tags=tags  # SQLAlchemy will handle JSON serialization
            )
            db.add(document)
            db.commit()
            db.refresh(document)
            logger.info(f"Created document: {title}")
            return document.id
        except SQLAlchemyError as e:
            db.rollback()
            logger.error(f"Error creating document: {str(e)}")
            raise
        finally:
            db.close()
    
    def get_document(self, title: str) -> Optional[Dict[str, Any]]:
        """Get a document by title"""
        db = self._get_db()
        try:
            document = db.query(Document).filter(Document.title == title).first()
            if document:
                return {
                    'id': document.id,
                    'title': document.title,
                    'content': document.content,
                    'tags': document.tags,  # Already deserialized by SQLAlchemy
                    'created_at': document.created_at.isoformat(),
                    'updated_at': document.updated_at.isoformat()
                }
            return None
        except SQLAlchemyError as e:
            logger.error(f"Error retrieving document: {str(e)}")
            raise
        finally:
            db.close()
    
    def get_all_titles(self) -> List[str]:
        """Get all document titles"""
        db = self._get_db()
        try:
            titles = db.query(Document.title).all()
            return [title[0] for title in titles]
        except SQLAlchemyError as e:
            logger.error(f"Error retrieving titles: {str(e)}")
            raise
        finally:
            db.close()
    def get_titles_by_tags(self, tags: List[str]) -> List[str]:
        """Get document titles filtered by tags"""
        db = self._get_db()
        try:
            if self.is_sqlite:
                # SQLite JSON array check using EXISTS and json_each
                tag_list = ','.join(f"'{tag}'" for tag in tags)
                documents = db.query(Document.title).filter(
                    text(f"EXISTS (SELECT 1 FROM json_each(documents.tags) WHERE json_each.value IN ({tag_list}))")
                ).all()
            else:
                # PostgreSQL JSONB array containment
                documents = db.query(Document.title).filter(
                    Document.tags.cast(JSONB).contains(tags)
                ).all()
            return [doc[0] for doc in documents]
        except SQLAlchemyError as e:
            logger.error(f"Error retrieving titles by tags: {str(e)}")
            raise
        finally:
            db.close()
    def get_documents_by_tags(self, tags: List[str]) -> List[Dict[str, Any]]:
        """Get all documents filtered by tags"""
        db = self._get_db()
        try:
            if self.is_sqlite:
                # SQLite JSON array check using EXISTS and json_each
                tag_list = ','.join(f"'{tag}'" for tag in tags)
                documents = db.query(Document).filter(
                    text(f"EXISTS (SELECT 1 FROM json_each(documents.tags) WHERE json_each.value IN ({tag_list}))")
                ).all()
            else:
                # PostgreSQL JSONB array containment
                documents = db.query(Document).filter(
                    Document.tags.cast(JSONB).contains(tags)
                ).all()
            return [{
                'id': doc.id,
                'title': doc.title,
                'content': doc.content,
                'tags': doc.tags,
                'created_at': doc.created_at.isoformat(),
                'updated_at': doc.updated_at.isoformat()
            } for doc in documents]
        except SQLAlchemyError as e:
            logger.error(f"Error retrieving documents by tags: {str(e)}")
            raise
        finally:
            db.close()
    def search_documents(self, query: str) -> List[str]:
        """Search documents by keyword and return matching titles"""
        db = self._get_db()
        try:
            if self.is_sqlite:
                # SQLite basic text search
                documents = db.query(Document.title).filter(
                    Document.content.like(f"%{query}%")
                ).all()
            else:
                # PostgreSQL full text search
                documents = db.query(Document.title).filter(
                    text("to_tsvector('english', content) @@ plainto_tsquery('english', :query)")
                ).params(query=query).all()
            return [doc[0] for doc in documents]
        except SQLAlchemyError as e:
            logger.error(f"Error searching documents: {str(e)}")
            raise
        finally:
            db.close()
    def update_document(self, title: str, content: Optional[str] = None,
                        tags: Optional[List[str]] = None) -> bool:
        """Update an existing document"""
        db = self._get_db()
        try:
            logger.info(f"Attempting to update document. Title: {title}, Content length: {len(content) if content else 0}, Tags: {tags}")
            
            document = db.query(Document).filter(Document.title == title).first()
            if not document:
                logger.warning(f"Document not found with title: {title}")
                return False
            
            logger.info(f"Found document. Current state - ID: {document.id}, Title: {document.title}, Tags: {document.tags}")
            
            if content is not None:
                document.content = content
            if tags is not None:
                document.tags = tags
            
            document.updated_at = datetime.utcnow()
            
            logger.info(f"Committing changes - New content length: {len(document.content)}, New tags: {document.tags}")
            db.commit()
            logger.info(f"Successfully updated document: {title}")
            return True
        except SQLAlchemyError as e:
            db.rollback()
            import traceback
            logger.error(f"SQLAlchemy error updating document: {str(e)}\nTraceback:\n{traceback.format_exc()}")
            raise
        except Exception as e:
            db.rollback()
            import traceback
            logger.error(f"Unexpected error updating document: {str(e)}\nTraceback:\n{traceback.format_exc()}")
            raise
        finally:
            db.close()
    
    def get_all_documents(self) -> List[Dict[str, Any]]:
        """Get all documents"""
        db = self._get_db()
        try:
            documents = db.query(Document).all()
            return [{
                'id': doc.id,
                'title': doc.title,
                'content': doc.content,
                'tags': doc.tags,
                'created_at': doc.created_at.isoformat(),
                'updated_at': doc.updated_at.isoformat()
            } for doc in documents]
        except SQLAlchemyError as e:
            logger.error(f"Error retrieving all documents: {str(e)}")
            raise
        finally:
            db.close()

    def delete_document(self, title: str) -> bool:
        """Delete a document by title"""
        db = self._get_db()
        try:
            document = db.query(Document).filter(Document.title == title).first()
            if not document:
                return False
            
            db.delete(document)
            db.commit()
            logger.info(f"Deleted document: {title}")
            return True
        except SQLAlchemyError as e:
            db.rollback()
            logger.error(f"Error deleting document: {str(e)}")
            raise
        finally:
            db.close()