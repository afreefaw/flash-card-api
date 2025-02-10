# Flashcards API

A simple spaced repetition flashcard API that helps you learn and retain information effectively. Cards are stored in a database (supports both SQLite and PostgreSQL) and served through a REST API.

## Features

- Create and manage flashcards with questions and answers
- Tag-based organization
- Spaced repetition algorithm for optimal learning
- Secure API key authentication via query parameter
- Persistent storage using SQLite (local) or PostgreSQL (production)
- Comprehensive logging for debugging

## Local Development

1. Clone the repository
2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Create a `.env` file:
```bash
# Database Configuration
DATABASE_URL=sqlite:///flashcards.db

# API Key Configuration
API_KEY=your-development-key-here
```

4. Start the server:
```bash
python api.py
```

The server will run on `http://localhost:8000`.

## Authentication

All API endpoints require an API key passed as a query parameter:

```
?api_key=your-api-key-here
```

Example: `http://localhost:8000/next_card?api_key=your-api-key-here`

The API key must match the one set in your environment variables.

## API Endpoints

### Create Card
```
POST /create_card?api_key=your-api-key-here

Body:
{
    "question": "What is the capital of France?",
    "answer": "Paris",
    "tags": ["geography", "europe"]
}
```

### Update Card
```
PUT /update_card/{card_id}?api_key=your-api-key-here

Body:
{
    "question": "Updated question",
    "answer": "Updated answer",
    "tags": ["new", "tags"]
}
```

### Get Next Card
```
GET /next_card?api_key=your-api-key-here
```

### Get Next Card by Tag
```
GET /next_card_by_tag?tag=geography&api_key=your-api-key-here
```

### Mark Success/Failure
```
POST /mark_success/{card_id}?api_key=your-api-key-here
POST /mark_failure/{card_id}?api_key=your-api-key-here
```

### Set Due Date
```
POST /set_due_date/{card_id}?api_key=your-api-key-here

Body:
{
    "due_date": "2025-02-10T00:00:00.000000"
}
```

### Delete Card
```
DELETE /delete_card/{card_id}?api_key=your-api-key-here
```

## Example Usage

```python
import requests
import os
from dotenv import load_dotenv

# Load API key from environment
load_dotenv()
API_KEY = os.getenv("API_KEY")

API_URL = "http://localhost:8000"  # Or your Render.com URL in production

# Create a new card
response = requests.post(
    f"{API_URL}/create_card",
    params={"api_key": API_KEY},
    json={
        "question": "What is the capital of Japan?",
        "answer": "Tokyo",
        "tags": ["geography", "asia"]
    }
)
card = response.json()
print(f"Created card: {card}")

# Get next due card
response = requests.get(
    f"{API_URL}/next_card",
    params={"api_key": API_KEY}
)
next_card = response.json()
print(f"Next card: {next_card}")
```

## Deployment

Deploy to Render.com with these environment variables:
- `DATABASE_URL`: Your PostgreSQL URL
- `API_KEY`: Your production API key (generate with `openssl rand -hex 32`)

## Security Notes

- Never use the development API key in production
- Generate a secure random API key for production use
- Keep your .env file out of version control
- The API will refuse to start in production without a proper API key set

## Spaced Repetition Algorithm

The API uses a spaced repetition algorithm with the following intervals (in days):
```python
[1/48, 1, 3, 7, 14, 30, 120, 365]
```

- New card → Due in 30 minutes
- Success → Move to next interval
- Failure → Reset to first interval
- At 365 days → Stay at that interval

## Logging

The API maintains two log files:
- `api.log`: API request/response logs
- `flashcards.log`: Database operation logs

## Backup and Restore

The API provides endpoints and a command-line script to backup and restore your flashcards.

### API Endpoints

#### Download Cards
```
GET /download_cards?api_key=your-api-key-here
```
Downloads all cards from the database.

#### Upload Cards
```
POST /upload_cards?api_key=your-api-key-here

Body:
{
    "cards": [
        {
            "id": 1,
            "question": "What is the capital of France?",
            "answer": "Paris",
            "tags": ["geography", "europe"],
            "success_count": 3,
            "due_date": "2025-02-10T00:00:00.000000"
        },
        ...
    ]
}
```
Uploads cards to the database. Existing cards (matched by ID) will be updated, and new cards will be inserted.

### Command-Line Script

A Python script is provided in the `scripts` directory to easily backup and restore your flashcards:

1. Set up environment variables in `.env`:
```bash
API_KEY=your-api-key-here
API_URL=http://localhost:8000  # Or your production URL
```

2. Download all cards to a file:
```bash
python scripts/manage_cards.py download cards_backup.json
```

3. Upload cards from a backup file:
```bash
python scripts/manage_cards.py upload cards_backup.json
```

The backup file includes a timestamp and all card data in JSON format. This is useful for:
- Creating backups before server migrations
- Transferring cards between instances
- Keeping a local backup of your flashcards