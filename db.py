import sqlite3
import json
import logging
from datetime import datetime, timedelta
from pathlib import Path
from pythonjsonlogger import jsonlogger
from typing import Optional, List

# Set up logging
log_handler = logging.FileHandler('flashcards.log')
log_handler.setFormatter(jsonlogger.JsonFormatter('%(asctime)s %(levelname)s %(message)s'))
logger = logging.getLogger('flashcards')
logger.addHandler(log_handler)
logger.setLevel(logging.INFO)

class FlashcardsDB:
    # Intervals in days for spaced repetition
    INTERVALS = [1/48, 1, 3, 7, 14, 30, 120, 365]  # First interval is 30 minutes (1/48 of a day)
    
    def __init__(self, db_path='flashcards.db'):
        self.db_path = db_path
        self._initialize_db()
    
    def _initialize_db(self):
        """Initialize the database with required tables if they don't exist."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Create cards table
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS cards (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        question TEXT NOT NULL,
                        answer TEXT NOT NULL,
                        success_count INTEGER DEFAULT 0,
                        due_date TIMESTAMP NOT NULL,
                        tags TEXT NOT NULL,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                
                # Create metadata table for tracking last card
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS metadata (
                        key TEXT PRIMARY KEY,
                        value TEXT NOT NULL
                    )
                ''')
                
                conn.commit()
                logger.info('Database initialized successfully', extra={
                    'db_path': self.db_path,
                    'tables_created': ['cards', 'metadata']
                })
        except sqlite3.Error as e:
            logger.error('Failed to initialize database', extra={
                'error': str(e),
                'db_path': self.db_path
            })
            raise
    
    def create_card(self, question: str, answer: str, tags: list[str]) -> int:
        """Create a new flashcard and return its ID."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                # Store tags as JSON string
                tags_json = json.dumps(tags)
                # Set initial due date to current timestamp
                current_time = datetime.utcnow().isoformat()
                
                cursor.execute('''
                    INSERT INTO cards (question, answer, tags, due_date, success_count)
                    VALUES (?, ?, ?, ?, 0)
                ''', (question, answer, tags_json, current_time))
                
                card_id = cursor.lastrowid
                conn.commit()
                
                logger.info('Created new flashcard', extra={
                    'card_id': card_id,
                    'tags': tags
                })
                return card_id
        except sqlite3.Error as e:
            logger.error('Failed to create flashcard', extra={
                'error': str(e),
                'question': question,
                'tags': tags
            })
            raise

    def update_card(self, card_id: int, question: str = None, answer: str = None, tags: list[str] = None) -> bool:
        """Update an existing flashcard."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                updates = []
                params = []
                
                if question is not None:
                    updates.append('question = ?')
                    params.append(question)
                if answer is not None:
                    updates.append('answer = ?')
                    params.append(answer)
                if tags is not None:
                    updates.append('tags = ?')
                    params.append(json.dumps(tags))
                
                if not updates:
                    logger.warning('No updates provided for card', extra={'card_id': card_id})
                    return False
                
                query = f'''
                    UPDATE cards 
                    SET {', '.join(updates)}
                    WHERE id = ?
                '''
                params.append(card_id)
                
                cursor.execute(query, params)
                conn.commit()
                
                if cursor.rowcount == 0:
                    logger.warning('Card not found for update', extra={'card_id': card_id})
                    return False
                
                logger.info('Updated flashcard', extra={
                    'card_id': card_id,
                    'updated_fields': [u.split(' = ')[0] for u in updates]
                })
                return True
        except sqlite3.Error as e:
            logger.error('Failed to update flashcard', extra={
                'error': str(e),
                'card_id': card_id
            })
            raise

    def get_card(self, card_id: int) -> dict:
        """Retrieve a flashcard by ID."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT id, question, answer, success_count, due_date, tags
                    FROM cards
                    WHERE id = ?
                ''', (card_id,))
                
                row = cursor.fetchone()
                if not row:
                    logger.warning('Card not found', extra={'card_id': card_id})
                    return None
                
                card = {
                    'id': row[0],
                    'question': row[1],
                    'answer': row[2],
                    'success_count': row[3],
                    'due_date': row[4],
                    'tags': json.loads(row[5])
                }
                
                logger.info('Retrieved flashcard', extra={'card_id': card_id})
                return card
        except sqlite3.Error as e:
            logger.error('Failed to retrieve flashcard', extra={
                'error': str(e),
                'card_id': card_id
            })
            raise

    def set_last_card(self, card_id: int) -> bool:
        """Store the ID of the last reviewed card."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT OR REPLACE INTO metadata (key, value)
                    VALUES ('last_card_id', ?)
                ''', (str(card_id),))
                
                conn.commit()
                logger.info('Updated last card ID', extra={'card_id': card_id})
                return True
        except sqlite3.Error as e:
            logger.error('Failed to set last card ID', extra={
                'error': str(e),
                'card_id': card_id
            })
            raise

    def get_last_card(self) -> int:
        """Retrieve the ID of the last reviewed card."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT value FROM metadata WHERE key = 'last_card_id'
                ''')
                
                row = cursor.fetchone()
                if not row:
                    logger.info('No last card ID found')
                    return None
                
                card_id = int(row[0])
                logger.info('Retrieved last card ID', extra={'card_id': card_id})
                return card_id
        except sqlite3.Error as e:
            logger.error('Failed to get last card ID', extra={'error': str(e)})
            raise

    def get_next_due_card(self, tag: Optional[str] = None) -> Optional[dict]:
        """Get the next due card, optionally filtered by tag."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                query = '''
                    SELECT id, question, answer, success_count, due_date, tags
                    FROM cards
                    WHERE 1=1
                '''
                params = []
                
                if tag:
                    query += " AND tags LIKE ?"
                    params.append(f'%"{tag}"%')  # Look for tag in JSON array
                
                query += " ORDER BY due_date ASC LIMIT 1"
                
                cursor.execute(query, params)
                row = cursor.fetchone()
                
                if not row:
                    logger.info('No cards due', extra={'tag_filter': tag})
                    return None
                
                card = {
                    'id': row[0],
                    'question': row[1],
                    'answer': row[2],
                    'success_count': row[3],
                    'due_date': row[4],
                    'tags': json.loads(row[5])
                }
                
                self.set_last_card(card['id'])
                logger.info('Retrieved next due card', extra={
                    'card_id': card['id'],
                    'tag_filter': tag
                })
                return card
        except sqlite3.Error as e:
            logger.error('Failed to get next due card', extra={
                'error': str(e),
                'tag_filter': tag
            })
            raise

    def _calculate_next_due_date(self, success_count: int) -> str:
        """Calculate the next due date based on success count."""
        interval_idx = min(success_count, len(self.INTERVALS) - 1)
        interval_days = self.INTERVALS[interval_idx]
        next_due = datetime.utcnow() + timedelta(days=interval_days)
        return next_due.isoformat()

    def mark_card_success(self, card_id: int) -> bool:
        """Mark a card as successfully reviewed and update its due date."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Get current success count
                cursor.execute('SELECT success_count FROM cards WHERE id = ?', (card_id,))
                row = cursor.fetchone()
                if not row:
                    logger.warning('Card not found for success marking', extra={'card_id': card_id})
                    return False
                
                new_success_count = row[0] + 1
                new_due_date = self._calculate_next_due_date(new_success_count)
                
                cursor.execute('''
                    UPDATE cards
                    SET success_count = ?, due_date = ?
                    WHERE id = ?
                ''', (new_success_count, new_due_date, card_id))
                
                conn.commit()
                logger.info('Marked card as success', extra={
                    'card_id': card_id,
                    'new_success_count': new_success_count,
                    'new_due_date': new_due_date
                })
                return True
        except sqlite3.Error as e:
            logger.error('Failed to mark card as success', extra={
                'error': str(e),
                'card_id': card_id
            })
            raise

    def mark_card_failure(self, card_id: int) -> bool:
        """Mark a card as failed and reset its progress."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Reset success count and calculate new due date
                new_due_date = self._calculate_next_due_date(0)
                
                cursor.execute('''
                    UPDATE cards
                    SET success_count = 0, due_date = ?
                    WHERE id = ?
                ''', (new_due_date, card_id))
                
                conn.commit()
                logger.info('Marked card as failure', extra={
                    'card_id': card_id,
                    'new_due_date': new_due_date
                })
                return True
        except sqlite3.Error as e:
            logger.error('Failed to mark card as failure', extra={
                'error': str(e),
                'card_id': card_id
            })
            raise

    def set_card_due_date(self, card_id: int, due_date: str) -> bool:
        """Manually set a card's due date."""
        try:
            # Validate the date format
            datetime.fromisoformat(due_date)
            
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    UPDATE cards
                    SET due_date = ?
                    WHERE id = ?
                ''', (due_date, card_id))
                
                conn.commit()
                if cursor.rowcount == 0:
                    logger.warning('Card not found for due date update', extra={'card_id': card_id})
                    return False
                
                logger.info('Updated card due date', extra={
                    'card_id': card_id,
                    'new_due_date': due_date
                })
                return True
        except (ValueError, sqlite3.Error) as e:
            logger.error('Failed to set card due date', extra={
                'error': str(e),
                'card_id': card_id,
                'due_date': due_date
            })
            raise

    def delete_card(self, card_id: int) -> bool:
        """Delete a flashcard."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('DELETE FROM cards WHERE id = ?', (card_id,))
                
                conn.commit()
                if cursor.rowcount == 0:
                    logger.warning('Card not found for deletion', extra={'card_id': card_id})
                    return False
                
                logger.info('Deleted card', extra={'card_id': card_id})
                return True
        except sqlite3.Error as e:
            logger.error('Failed to delete card', extra={
                'error': str(e),
                'card_id': card_id
            })
            raise