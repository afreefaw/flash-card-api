# Flashcards API

A simple spaced repetition flashcard API that helps you learn and retain information effectively. Cards are stored in a database (supports both SQLite and PostgreSQL) and served through a REST API.

## Features

- Create and manage flashcards with questions and answers
- Tag-based organization
- Spaced repetition algorithm for optimal learning
- Secure API key authentication with environment variable support
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

## Deployment to Render.com

This API can be deployed to Render.com with PostgreSQL support. Here's how:

1. Create a PostgreSQL database:
   - Go to render.com and sign up
   - Click "New +" and select "PostgreSQL"
   - Choose a name and the free plan
   - Click "Create Database"
   - Copy the "External Database URL" (you'll need it later)

2. Create a new Web Service:
   - Click "New +" and select "Web Service"
   - Connect your GitHub repository
   - Choose a name
   - Set the following:
     - Build Command: `pip install -r requirements.txt`
     - Start Command: `uvicorn api:app --host 0.0.0.0 --port $PORT`
   - Add environment variables:
     - `DATABASE_URL`: Your PostgreSQL URL from step 1
     - `API_KEY`: Generate a secure random string (e.g., using `openssl rand -hex 32`)
   - Click "Create Web Service"

The API will automatically use PostgreSQL in production while maintaining SQLite support for local development.

### Security Notes

- Never use the development API key in production
- Generate a secure random API key for production use
- Keep your .env file out of version control (it's already in .gitignore)
- The API will refuse to start in production without a proper API key set

## Authentication

All API endpoints require an API key passed in the `X-API-Key` header:

```
X-API-Key: your-api-key-here
```

The API key must match the one set in your environment variables.

## API Endpoints

### Create Card
```
POST /create_card
```

Create a new flashcard.

Request body:
```json
{
    "question": "What is the capital of France?",
    "answer": "Paris",
    "tags": ["geography", "europe"]
}
```

Response:
```json
{
    "id": 1,
    "question": "What is the capital of France?",
    "answer": "Paris",
    "tags": ["geography", "europe"],
    "success_count": 0,
    "due_date": "2025-02-10T00:00:00.000000"
}
```

### Update Card
```
PUT /update_card/{card_id}
```

Update an existing flashcard. All fields are optional.

Request body:
```json
{
    "question": "Updated question",
    "answer": "Updated answer",
    "tags": ["new", "tags"]
}
```

Response: Returns the updated card object.

### Get Next Card
```
GET /next_card
```

Get the next due card (oldest due date first).

Response: Returns a card object or 404 if no cards are due.

### Get Next Card by Tag
```
GET /next_card_by_tag?tag=geography
```

Get the next due card with a specific tag.

Response: Returns a card object or 404 if no cards with the tag are due.

### Mark Success
```
POST /mark_success/{card_id}
```

Mark a card review as successful. This will:
- Increment the success count
- Increase the interval to the next one in the sequence
- Update the due date accordingly

Response:
```json
{
    "message": "Card marked as success"
}
```

### Mark Failure
```
POST /mark_failure/{card_id}
```

Mark a card review as failed. This will:
- Reset the success count to 0
- Reset the interval to the beginning
- Update the due date accordingly

Response:
```json
{
    "message": "Card marked as failure"
}
```

### Set Due Date
```
POST /set_due_date/{card_id}
```

Manually set a card's due date.

Request body:
```json
{
    "due_date": "2025-02-10T00:00:00.000000"
}
```

Response:
```json
{
    "message": "Card due date updated"
}
```

### Delete Card
```
DELETE /delete_card/{card_id}
```

Delete a flashcard permanently.

Response:
```json
{
    "message": "Card deleted successfully"
}
```

Returns 404 if the card is not found.

## Spaced Repetition Algorithm

The API uses a spaced repetition algorithm with the following intervals (in days):
```python
[1/48, 1, 3, 7, 14, 30, 120, 365]
```

- When a card is created, it is due after the first interval (30 minutes)
- After each successful review, the interval increases to the next one in the sequence
- After a failed review, the interval resets to the beginning
- Once a card reaches the last interval (365 days), it stays at that interval for subsequent successful reviews

For example:
1. New card → Due in 30 minutes
2. Success → Due in 1 day
3. Success → Due in 3 days
4. Success → Due in 7 days
5. Failure → Resets to due in 30 minutes

## Example Usage

Here's a Python example of using the API:

```python
import requests
import os
from dotenv import load_dotenv

# Load API key from environment
load_dotenv()
API_KEY = os.getenv("API_KEY")

API_URL = "http://localhost:8000"  # Or your Render.com URL in production
HEADERS = {"X-API-Key": API_KEY}

# Create a new card
response = requests.post(
    f"{API_URL}/create_card",
    headers=HEADERS,
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
    headers=HEADERS
)
next_card = response.json()
print(f"Next card: {next_card}")

# Mark as success
response = requests.post(
    f"{API_URL}/mark_success/{next_card['id']}",
    headers=HEADERS
)
print("Marked card as success")
```

## Logging

The API maintains two log files:
- `api.log`: API request/response logs
- `flashcards.log`: Database operation logs

These logs include timestamps, log levels, and detailed context for debugging.