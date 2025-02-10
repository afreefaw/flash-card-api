# Flashcards API

A simple spaced repetition flashcard API that helps you learn and retain information effectively. Cards are stored in an SQLite database and served through a REST API.

## Features

- Create and manage flashcards with questions and answers
- Tag-based organization
- Spaced repetition algorithm for optimal learning
- Simple API key authentication
- Persistent storage using SQLite
- Comprehensive logging for debugging

## Installation

1. Clone the repository
2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Start the server:
```bash
python api.py
```

The server will run on `http://localhost:8000`.

## Authentication

All API endpoints require an API key passed in the `X-API-Key` header:

```
X-API-Key: your-secret-key-here
```

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

API_URL = "http://localhost:8000"
HEADERS = {"X-API-Key": "your-secret-key-here"}

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