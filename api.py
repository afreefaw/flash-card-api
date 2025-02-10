from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import List, Optional
import logging
from pythonjsonlogger import jsonlogger
import time
from db import FlashcardsDB
from document_api import get_document_router
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Set up logging
api_logger = logging.getLogger('flashcards.api')
api_logger.setLevel(logging.INFO)
handler = logging.FileHandler('api.log')
handler.setFormatter(jsonlogger.JsonFormatter('%(asctime)s %(levelname)s %(message)s %(path)s %(method)s %(response_time)ms'))
api_logger.addHandler(handler)

# Initialize FastAPI app
app = FastAPI(title="Flashcards API")

# Initialize database
db = FlashcardsDB()

# Configuration
API_KEY = os.getenv("API_KEY", "your-secret-key-here")  # Default key for development
if API_KEY == "your-secret-key-here" and os.getenv("RENDER"):
    raise ValueError("Production API_KEY must be set in environment variables")

# Models
class CardBase(BaseModel):
    question: str
    answer: str
    tags: List[str]

class CardUpdate(BaseModel):
    question: Optional[str] = None
    answer: Optional[str] = None
    tags: Optional[List[str]] = None

class CardResponse(CardBase):
    id: int
    success_count: int
    due_date: str

class DueDateUpdate(BaseModel):
    due_date: str

# Middleware for logging
@app.middleware("http")
async def log_requests(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    end_time = time.time()
    
    api_logger.info(
        'API Request',
        extra={
            'path': request.url.path,
            'method': request.method,
            'response_time': round((end_time - start_time) * 1000, 2),
            'status_code': response.status_code
        }
    )
    return response

# Authentication function
def verify_api_key(api_key: str) -> bool:
    if api_key != API_KEY:
        api_logger.warning('Authentication failed', extra={'provided_key': api_key})
        raise HTTPException(
            status_code=401,
            detail="Invalid API key"
        )
    return True

# Error handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    api_logger.error(
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
@app.post("/create_card", response_model=CardResponse)
async def create_card(card: CardBase, api_key: str):
    verify_api_key(api_key)
    try:
        card_id = db.create_card(
            question=card.question,
            answer=card.answer,
            tags=card.tags
        )
        return db.get_card(card_id)
    except Exception as e:
        api_logger.error('Failed to create card', extra={'error': str(e)})
        raise HTTPException(status_code=500, detail="Failed to create card")

@app.put("/update_card/{card_id}", response_model=CardResponse)
async def update_card(card_id: int, card_update: CardUpdate, api_key: str):
    verify_api_key(api_key)
    try:
        success = db.update_card(
            card_id=card_id,
            question=card_update.question,
            answer=card_update.answer,
            tags=card_update.tags
        )
        if not success:
            raise HTTPException(status_code=404, detail="Card not found")
        return db.get_card(card_id)
    except HTTPException:
        raise
    except Exception as e:
        api_logger.error('Failed to update card', extra={'error': str(e), 'card_id': card_id})
        raise HTTPException(status_code=500, detail="Failed to update card")

@app.get("/next_card", response_model=CardResponse)
async def get_next_card(api_key: str):
    verify_api_key(api_key)
    try:
        card = db.get_next_due_card()
        if not card:
            raise HTTPException(status_code=404, detail="No cards due")
        return card
    except Exception as e:
        api_logger.error('Failed to get next card', extra={'error': str(e)})
        raise HTTPException(status_code=500, detail="Failed to get next card")

@app.get("/next_card_by_tag", response_model=CardResponse)
async def get_next_card_by_tag(tag: str, api_key: str):
    verify_api_key(api_key)
    try:
        card = db.get_next_due_card(tag=tag)
        if not card:
            raise HTTPException(status_code=404, detail="No cards due for the specified tag")
        return card
    except Exception as e:
        api_logger.error('Failed to get next card by tag', extra={'error': str(e), 'tag': tag})
        raise HTTPException(status_code=500, detail="Failed to get next card by tag")

@app.post("/mark_success/{card_id}")
async def mark_success(card_id: int, api_key: str):
    verify_api_key(api_key)
    try:
        success = db.mark_card_success(card_id)
        if not success:
            raise HTTPException(status_code=404, detail="Card not found")
        return {"message": "Card marked as success"}
    except Exception as e:
        api_logger.error('Failed to mark card as success', extra={'error': str(e), 'card_id': card_id})
        raise HTTPException(status_code=500, detail="Failed to mark card as success")

@app.post("/mark_failure/{card_id}")
async def mark_failure(card_id: int, api_key: str):
    verify_api_key(api_key)
    try:
        success = db.mark_card_failure(card_id)
        if not success:
            raise HTTPException(status_code=404, detail="Card not found")
        return {"message": "Card marked as failure"}
    except Exception as e:
        api_logger.error('Failed to mark card as failure', extra={'error': str(e), 'card_id': card_id})
        raise HTTPException(status_code=500, detail="Failed to mark card as failure")

@app.post("/set_due_date/{card_id}")
async def set_due_date(card_id: int, due_date_update: DueDateUpdate, api_key: str):
    verify_api_key(api_key)
    try:
        success = db.set_card_due_date(card_id, due_date_update.due_date)
        if not success:
            raise HTTPException(status_code=404, detail="Card not found")
        return {"message": "Card due date updated"}
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format. Use ISO format (YYYY-MM-DDTHH:MM:SS)")
    except Exception as e:
        api_logger.error('Failed to set card due date', extra={'error': str(e), 'card_id': card_id})
        raise HTTPException(status_code=500, detail="Failed to set card due date")

@app.delete("/delete_card/{card_id}")
async def delete_card(card_id: int, api_key: str):
    verify_api_key(api_key)
    try:
        success = db.delete_card(card_id)
        if not success:
            raise HTTPException(status_code=404, detail="Card not found")
        return {"message": "Card deleted successfully"}
    except Exception as e:
        api_logger.error('Failed to delete card', extra={'error': str(e), 'card_id': card_id})
        raise HTTPException(status_code=500, detail="Failed to delete card")

@app.get("/download_cards")
async def download_cards(api_key: str):
    verify_api_key(api_key)
    try:
        cards = db.get_all_cards()
        return {"cards": cards}
    except Exception as e:
        api_logger.error('Failed to download cards', extra={'error': str(e)})
        raise HTTPException(status_code=500, detail="Failed to download cards")

class BulkCardsUpload(BaseModel):
    cards: List[CardResponse]

@app.post("/upload_cards")
async def upload_cards(cards_data: BulkCardsUpload, api_key: str):
    verify_api_key(api_key)
    try:
        api_logger.info('Starting cards upload', extra={
            'card_count': len(cards_data.cards),
            'first_card_id': cards_data.cards[0].id if cards_data.cards else None
        })
        
        # Log the first card's data for debugging
        if cards_data.cards:
            first_card = cards_data.cards[0]
            api_logger.info('First card data', extra={
                'id': first_card.id,
                'question': first_card.question,
                'success_count': first_card.success_count,
                'due_date': first_card.due_date,
                'tag_count': len(first_card.tags)
            })
        
        result = db.bulk_upsert_cards(cards_data.cards)
        api_logger.info('Cards upload completed', extra={
            'inserted': result['inserted'],
            'updated': result['updated']
        })
        return {
            "message": f"Successfully processed cards",
            "inserted": result['inserted'],
            "updated": result['updated']
        }
    except Exception as e:
        api_logger.error('Failed to upload cards', extra={
            'error': str(e),
            'error_type': type(e).__name__,
            'card_count': len(cards_data.cards) if cards_data else 0
        })
        raise HTTPException(status_code=500, detail="Failed to upload cards")

# Mount the document API router
app.include_router(get_document_router())

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)