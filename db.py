from sqlalchemy import create_engine, Column, Integer, String, DateTime, JSON, MetaData
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime, timedelta
import logging
from pythonjsonlogger import jsonlogger
from typing import Optional, List
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Set up logging
logger = logging.getLogger('flashcards')
logger.setLevel(logging.INFO)

# File handler
file_handler = logging.FileHandler('flashcards.log')
file_handler.setFormatter(jsonlogger.JsonFormatter('%(asctime)s %(levelname)s %(message)s'))
logger.addHandler(file_handler)

# Console handler
console_handler = logging.StreamHandler()
console_handler.setFormatter(logging.Formatter('%(levelname)s: %(message)s'))
logger.addHandler(console_handler)

# Database setup
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///flashcards.db")
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class Card(Base):
    __tablename__ = "cards"
    
    id = Column(Integer, primary_key=True, index=True)
    question = Column(String, nullable=False)
    answer = Column(String, nullable=False)
    success_count = Column(Integer, default=0)
    due_date = Column(DateTime, nullable=False)
    tags = Column(JSON, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

class Metadata(Base):
    __tablename__ = "metadata"
    
    key = Column(String, primary_key=True)
    value = Column(String, nullable=False)

# Create tables
Base.metadata.create_all(bind=engine)

class FlashcardsDB:
    # Intervals in days for spaced repetition
    INTERVALS = [1/48, 1, 3, 7, 14, 30, 120, 365]  # First interval is 30 minutes (1/48 of a day)
    
    def __init__(self, db_url=None):
        if db_url:
            self.engine = create_engine(db_url)
            self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
        else:
            self.engine = engine
            self.SessionLocal = SessionLocal
    
    def _get_db(self):
        db = self.SessionLocal()
        try:
            return db
        except:
            db.close()
            raise

    def create_card(self, question: str, answer: str, tags: List[str]) -> int:
        """Create a new flashcard and return its ID."""
        try:
            db = self._get_db()
            card = Card(
                question=question,
                answer=answer,
                tags=tags,
                due_date=datetime.utcnow(),
                success_count=0
            )
            db.add(card)
            db.commit()
            db.refresh(card)
            
            logger.info('Created new flashcard', extra={
                'card_id': card.id,
                'tags': tags
            })
            return card.id
        except Exception as e:
            logger.error('Failed to create flashcard', extra={
                'error': str(e),
                'question': question,
                'tags': tags
            })
            raise
        finally:
            db.close()

    def update_card(self, card_id: int, question: str = None, answer: str = None, tags: List[str] = None) -> bool:
        """Update an existing flashcard."""
        try:
            db = self._get_db()
            card = db.query(Card).filter(Card.id == card_id).first()
            
            if not card:
                logger.warning('Card not found for update', extra={'card_id': card_id})
                return False
            
            updated_fields = []
            if question is not None:
                card.question = question
                updated_fields.append('question')
            if answer is not None:
                card.answer = answer
                updated_fields.append('answer')
            if tags is not None:
                card.tags = tags
                updated_fields.append('tags')
            
            if not updated_fields:
                logger.warning('No updates provided for card', extra={'card_id': card_id})
                return False
            
            db.commit()
            
            logger.info('Updated flashcard', extra={
                'card_id': card_id,
                'updated_fields': updated_fields
            })
            return True
        except Exception as e:
            logger.error('Failed to update flashcard', extra={
                'error': str(e),
                'card_id': card_id
            })
            raise
        finally:
            db.close()

    def get_card(self, card_id: int) -> dict:
        """Retrieve a flashcard by ID."""
        try:
            db = self._get_db()
            card = db.query(Card).filter(Card.id == card_id).first()
            
            if not card:
                logger.warning('Card not found', extra={'card_id': card_id})
                return None
            
            result = {
                'id': card.id,
                'question': card.question,
                'answer': card.answer,
                'success_count': card.success_count,
                'due_date': card.due_date.isoformat(),
                'tags': card.tags
            }
            
            logger.info('Retrieved flashcard', extra={'card_id': card_id})
            return result
        except Exception as e:
            logger.error('Failed to retrieve flashcard', extra={
                'error': str(e),
                'card_id': card_id
            })
            raise
        finally:
            db.close()

    def set_last_card(self, card_id: int) -> bool:
        """Store the ID of the last reviewed card."""
        try:
            db = self._get_db()
            metadata = db.query(Metadata).filter(Metadata.key == 'last_card_id').first()
            
            if metadata:
                metadata.value = str(card_id)
            else:
                metadata = Metadata(key='last_card_id', value=str(card_id))
                db.add(metadata)
            
            db.commit()
            logger.info('Updated last card ID', extra={'card_id': card_id})
            return True
        except Exception as e:
            logger.error('Failed to set last card ID', extra={
                'error': str(e),
                'card_id': card_id
            })
            raise
        finally:
            db.close()

    def get_last_card(self) -> Optional[int]:
        """Retrieve the ID of the last reviewed card."""
        try:
            db = self._get_db()
            metadata = db.query(Metadata).filter(Metadata.key == 'last_card_id').first()
            
            if not metadata:
                logger.info('No last card ID found')
                return None
            
            card_id = int(metadata.value)
            logger.info('Retrieved last card ID', extra={'card_id': card_id})
            return card_id
        except Exception as e:
            logger.error('Failed to get last card ID', extra={'error': str(e)})
            raise
        finally:
            db.close()

    def get_next_due_card(self, tag: Optional[str] = None) -> Optional[dict]:
        """Get the next due card, optionally filtered by tag."""
        try:
            db = self._get_db()
            query = db.query(Card).order_by(Card.due_date)
            
            if tag:
                # PostgreSQL JSON array contains
                query = query.filter(Card.tags.contains([tag]))
            
            card = query.first()
            
            if not card:
                logger.info('No cards due', extra={'tag_filter': tag})
                return None
            
            result = {
                'id': card.id,
                'question': card.question,
                'answer': card.answer,
                'success_count': card.success_count,
                'due_date': card.due_date.isoformat(),
                'tags': card.tags
            }
            
            self.set_last_card(card.id)
            logger.info('Retrieved next due card', extra={
                'card_id': card.id,
                'tag_filter': tag
            })
            return result
        except Exception as e:
            logger.error('Failed to get next due card', extra={
                'error': str(e),
                'tag_filter': tag
            })
            raise
        finally:
            db.close()

    def _calculate_next_due_date(self, success_count: int) -> datetime:
        """Calculate the next due date based on success count."""
        interval_idx = min(success_count, len(self.INTERVALS) - 1)
        interval_days = self.INTERVALS[interval_idx]
        return datetime.utcnow() + timedelta(days=interval_days)

    def mark_card_success(self, card_id: int) -> bool:
        """Mark a card as successfully reviewed and update its due date."""
        try:
            db = self._get_db()
            card = db.query(Card).filter(Card.id == card_id).first()
            
            if not card:
                logger.warning('Card not found for success marking', extra={'card_id': card_id})
                return False
            
            card.success_count += 1
            card.due_date = self._calculate_next_due_date(card.success_count)
            
            db.commit()
            logger.info('Marked card as success', extra={
                'card_id': card_id,
                'new_success_count': card.success_count,
                'new_due_date': card.due_date.isoformat()
            })
            return True
        except Exception as e:
            logger.error('Failed to mark card as success', extra={
                'error': str(e),
                'card_id': card_id
            })
            raise
        finally:
            db.close()

    def mark_card_failure(self, card_id: int) -> bool:
        """Mark a card as failed and reset its progress."""
        try:
            db = self._get_db()
            card = db.query(Card).filter(Card.id == card_id).first()
            
            if not card:
                logger.warning('Card not found for failure marking', extra={'card_id': card_id})
                return False
            
            card.success_count = 0
            card.due_date = self._calculate_next_due_date(0)
            
            db.commit()
            logger.info('Marked card as failure', extra={
                'card_id': card_id,
                'new_due_date': card.due_date.isoformat()
            })
            return True
        except Exception as e:
            logger.error('Failed to mark card as failure', extra={
                'error': str(e),
                'card_id': card_id
            })
            raise
        finally:
            db.close()

    def set_card_due_date(self, card_id: int, due_date: str) -> bool:
        """Manually set a card's due date."""
        try:
            due_date_dt = datetime.fromisoformat(due_date)
            db = self._get_db()
            card = db.query(Card).filter(Card.id == card_id).first()
            
            if not card:
                logger.warning('Card not found for due date update', extra={'card_id': card_id})
                return False
            
            card.due_date = due_date_dt
            db.commit()
            
            logger.info('Updated card due date', extra={
                'card_id': card_id,
                'new_due_date': due_date
            })
            return True
        except ValueError as e:
            logger.error('Failed to set card due date - invalid date format', extra={
                'error': str(e),
                'card_id': card_id,
                'due_date': due_date
            })
            raise
        except Exception as e:
            logger.error('Failed to set card due date', extra={
                'error': str(e),
                'card_id': card_id,
                'due_date': due_date
            })
            raise
        finally:
            db.close()

    def delete_card(self, card_id: int) -> bool:
        """Delete a flashcard."""
        try:
            db = self._get_db()
            card = db.query(Card).filter(Card.id == card_id).first()
            
            if not card:
                logger.warning('Card not found for deletion', extra={'card_id': card_id})
                return False
            
            db.delete(card)
            db.commit()
            
            logger.info('Deleted card', extra={'card_id': card_id})
            return True
        except Exception as e:
            logger.error('Failed to delete card', extra={
                'error': str(e),
                'card_id': card_id
            })
            raise
        finally:
            db.close()

    def get_all_cards(self) -> List[dict]:
        """Get all flashcards in the database."""
        try:
            db = self._get_db()
            cards = db.query(Card).all()
            
            result = [{
                'id': card.id,
                'question': card.question,
                'answer': card.answer,
                'success_count': card.success_count,
                'due_date': card.due_date.isoformat(),
                'tags': card.tags
            } for card in cards]
            
            logger.info('Retrieved all flashcards', extra={'count': len(result)})
            return result
        except Exception as e:
            logger.error('Failed to retrieve all flashcards', extra={'error': str(e)})
            raise
        finally:
            db.close()

    def bulk_upsert_cards(self, cards: List[dict]) -> dict:
        """Insert or update multiple cards at once."""
        try:
            db = self._get_db()
            inserted = 0
            updated = 0
            
            logger.info('Starting bulk upsert', extra={
                'total_cards': len(cards),
                'first_card_id': cards[0].id if cards else None
            })
            
            for idx, card_data in enumerate(cards):
                try:
                    card_id = card_data.id
                    logger.debug(f'Processing card {idx+1}/{len(cards)}', extra={
                        'card_id': card_id,
                        'question': card_data.question,
                        'success_count': card_data.success_count,
                        'tag_count': len(card_data.tags)
                    })
                    
                    card = db.query(Card).filter(Card.id == card_id).first()
                    
                    if card:
                        # Update existing card
                        logger.debug(f'Updating existing card', extra={
                            'card_id': card_id,
                            'old_due_date': card.due_date.isoformat(),
                            'new_due_date': card_data.due_date
                        })
                        card.question = card_data.question
                        card.answer = card_data.answer
                        card.success_count = card_data.success_count
                        card.due_date = datetime.fromisoformat(card_data.due_date)
                        card.tags = card_data.tags
                        updated += 1
                    else:
                        # Create new card
                        logger.debug(f'Creating new card', extra={
                            'due_date': card_data.due_date,
                            'tag_count': len(card_data.tags)
                        })
                        new_card = Card(
                            question=card_data.question,
                            answer=card_data.answer,
                            success_count=card_data.success_count,
                            due_date=datetime.fromisoformat(card_data.due_date),
                            tags=card_data.tags
                        )
                        db.add(new_card)
                        inserted += 1
                except Exception as card_error:
                    import traceback
                    logger.error('Error processing individual card', extra={
                        'card_index': idx,
                        'card_id': card_data.id if hasattr(card_data, 'id') else None,
                        'error': str(card_error),
                        'error_type': type(card_error).__name__,
                        'traceback': traceback.format_exc(),
                        'card_data': str(card_data)
                    })
                    raise
            
            db.commit()
            logger.info('Bulk upsert completed', extra={
                'inserted': inserted,
                'updated': updated,
                'total_processed': inserted + updated
            })
            return {'inserted': inserted, 'updated': updated}
        except Exception as e:
            import traceback
            logger.error('Failed to bulk upsert cards', extra={
                'error': str(e),
                'error_type': type(e).__name__,
                'traceback': traceback.format_exc(),
                'total_cards': len(cards) if cards else 0,
                'first_card_data': str(cards[0]) if cards else None
            })
            raise
        finally:
            db.close()