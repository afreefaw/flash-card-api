from fastapi import FastAPI, HTTPException, Request, APIRouter
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import List, Optional
import logging
from pythonjsonlogger import jsonlogger
import time
from document_db import DocumentDB
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Set up logging
doc_api_logger = logging.getLogger('documents.api')
doc_api_logger.setLevel(logging.INFO)
handler = logging.FileHandler('documents_api.log')
handler.setFormatter(jsonlogger.JsonFormatter('%(asctime)s %(levelname)s %(message)s %(path)s %(method)s %(response_time)ms'))
doc_api_logger.addHandler(handler)

# Initialize router instead of app
router = APIRouter(prefix="/documents")

# Initialize database with SQLite for local development
db = DocumentDB('sqlite:///documents.db')

# Configuration
API_KEY = os.getenv("API_KEY", "your-secret-key-here")  # Default key for development
if API_KEY == "your-secret-key-here" and os.getenv("RENDER"):
    raise ValueError("Production API_KEY must be set in environment variables")

# Models
class DocumentBase(BaseModel):
    title: str
    content: str
    tags: List[str]

class DocumentUpdate(BaseModel):
    content: Optional[str] = None
    tags: Optional[List[str]] = None

class DocumentResponse(DocumentBase):
    id: int
    created_at: str
    updated_at: str

class DocumentUpload(BaseModel):
    documents: List[DocumentResponse]

# Authentication function
def verify_api_key(api_key: str) -> bool:
    if api_key != API_KEY:
        doc_api_logger.warning('Authentication failed', extra={'provided_key': api_key})
        raise HTTPException(
            status_code=401,
            detail="Invalid API key"
        )
    return True

# Error handler
async def document_exception_handler(request: Request, exc: Exception):
    doc_api_logger.error(
        'Unhandled exception',
        extra={
            'path': request.url.path,
            'method': request.method,
            'error': str(exc)
        }
    )
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"}
    )

# Endpoints
@router.get("/titles")
async def get_all_titles(api_key: str):
    verify_api_key(api_key)
    try:
        titles = db.get_all_titles()
        return {"titles": titles}
    except Exception as e:
        doc_api_logger.error('Failed to get titles', extra={'error': str(e)})
        raise HTTPException(status_code=500, detail="Failed to get titles")

@router.get("/titles/by_tags")
async def get_titles_by_tags(tags: str, api_key: str):
    verify_api_key(api_key)
    try:
        tag_list = [tag.strip() for tag in tags.split(",")]
        titles = db.get_titles_by_tags(tag_list)
        return {"titles": titles}
    except Exception as e:
        doc_api_logger.error('Failed to get titles by tags', extra={'error': str(e), 'tags': tags})
        raise HTTPException(status_code=500, detail="Failed to get titles by tags")

@router.get("/by_tags")
async def get_documents_by_tags(tags: str, api_key: str):
    verify_api_key(api_key)
    try:
        tag_list = [tag.strip() for tag in tags.split(",")]
        documents = db.get_documents_by_tags(tag_list)
        return {"documents": documents}
    except Exception as e:
        doc_api_logger.error('Failed to get documents by tags', extra={'error': str(e), 'tags': tags})
        raise HTTPException(status_code=500, detail="Failed to get documents by tags")

@router.get("/{title}")
async def get_document(title: str, api_key: str):
    verify_api_key(api_key)
    try:
        document = db.get_document(title)
        if not document:
            raise HTTPException(status_code=404, detail="Document not found")
        return document
    except HTTPException:
        raise
    except Exception as e:
        doc_api_logger.error('Failed to get document', extra={'error': str(e), 'title': title})
        raise HTTPException(status_code=500, detail="Failed to get document")

@router.get("/search")
async def search_documents(query: str, api_key: str):
    verify_api_key(api_key)
    try:
        titles = db.search_documents(query)
        return {"titles": titles}
    except Exception as e:
        doc_api_logger.error('Failed to search documents', extra={'error': str(e), 'query': query})
        raise HTTPException(status_code=500, detail="Failed to search documents")

@router.post("", response_model=DocumentResponse)
async def create_document(document: DocumentBase, api_key: str):
    verify_api_key(api_key)
    try:
        doc_id = db.create_document(
            title=document.title,
            content=document.content,
            tags=document.tags
        )
        created_doc = db.get_document(document.title)
        return created_doc
    except Exception as e:
        doc_api_logger.error('Failed to create document', extra={'error': str(e)})
        raise HTTPException(status_code=500, detail="Failed to create document")

@router.put("/{title}")
async def update_document(title: str, document_update: DocumentUpdate, api_key: str):
    verify_api_key(api_key)
    try:
        success = db.update_document(
            title=title,
            content=document_update.content,
            tags=document_update.tags
        )
        if not success:
            raise HTTPException(status_code=404, detail="Document not found")
        updated_doc = db.get_document(title)
        return updated_doc
    except HTTPException:
        raise
    except Exception as e:
        doc_api_logger.error('Failed to update document', extra={'error': str(e), 'title': title})
        raise HTTPException(status_code=500, detail="Failed to update document")

@router.delete("/{title}")
async def delete_document(title: str, api_key: str):
    verify_api_key(api_key)
    try:
        success = db.delete_document(title)
        if not success:
            raise HTTPException(status_code=404, detail="Document not found")
        return {"message": "Document deleted successfully"}
    except Exception as e:
        doc_api_logger.error('Failed to delete document', extra={'error': str(e), 'title': title})
        raise HTTPException(status_code=500, detail="Failed to delete document")

@router.get("/download")
async def download_documents(api_key: str):
    """Download all documents from the database."""
    verify_api_key(api_key)
    try:
        documents = db.get_all_documents()
        return {"documents": documents}
    except Exception as e:
        doc_api_logger.error('Failed to download documents', extra={'error': str(e)})
        raise HTTPException(status_code=500, detail="Failed to download documents")

@router.post("/upload")
async def upload_documents(documents: DocumentUpload, api_key: str):
    """Upload documents to the database. Existing documents will be updated."""
    verify_api_key(api_key)
    try:
        inserted = 0
        updated = 0
        for doc in documents.documents:
            existing = db.get_document(doc.title)
            if existing:
                db.update_document(
                    title=doc.title,
                    content=doc.content,
                    tags=doc.tags
                )
                updated += 1
            else:
                db.create_document(
                    title=doc.title,
                    content=doc.content,
                    tags=doc.tags
                )
                inserted += 1
        return {"inserted": inserted, "updated": updated}
    except Exception as e:
        doc_api_logger.error('Failed to upload documents', extra={'error': str(e)})
        raise HTTPException(status_code=500, detail="Failed to upload documents")

# Function to get the router
def get_document_router():
    return router