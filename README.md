# Flashcards and Knowledge Base API

A simple spaced repetition flashcard API that helps you learn and retain information effectively, combined with a text knowledge base for storing and organizing information. Data is stored in a database (supports both SQLite and PostgreSQL) and served through a REST API.

## Features

- Create and manage flashcards with questions and answers
- Tag-based organization
- Spaced repetition algorithm for optimal learning
- Text knowledge base for storing markdown-formatted documents
- Document organization with tags and full-text search
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

## Flashcard API Endpoints

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

## Document API Endpoints

All document endpoints are under the `/documents` prefix.

### Get All Titles
```
GET /documents/titles?api_key=your-api-key-here
```
Returns a list of all document titles.

### Get Titles by Tags
```
GET /documents/titles/by_tags?tags=tag1,tag2&api_key=your-api-key-here
```
Returns titles of documents that have all specified tags.

### Get Documents by Tags
```
GET /documents/by_tags?tags=tag1,tag2&api_key=your-api-key-here
```
Returns full documents that have all specified tags.

### Get Document
```
GET /documents/{title}?api_key=your-api-key-here
```
Returns a specific document by its title.

### Search Documents
```
GET /documents/search?query=keyword&api_key=your-api-key-here
```
Performs a full-text search and returns matching document titles.

### Create Document
```
POST /documents?api_key=your-api-key-here

Body:
{
    "title": "Meeting Notes - John Doe",
    "content": "# Meeting with John\n\nDiscussed project timeline...",
    "tags": ["meetings", "projects"]
}
```

### Update Document
```
PUT /documents/{title}?api_key=your-api-key-here

Body:
{
    "content": "Updated content...",
    "tags": ["updated", "tags"]
}
```
Both content and tags are optional. Only provided fields will be updated.

### Delete Document
```
DELETE /documents/{title}?api_key=your-api-key-here
```

## Example Usage

### Flashcards Example
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

### Documents Example
```python
import requests
import os
from dotenv import load_dotenv

# Load API key from environment
load_dotenv()
API_KEY = os.getenv("API_KEY")

API_URL = "http://localhost:8000"  # Or your Render.com URL in production

# Create a new document
response = requests.post(
    f"{API_URL}/documents",
    params={"api_key": API_KEY},
    json={
        "title": "Project Ideas",
        "content": "# Future Projects\n\n1. Build a task manager\n2. Create a blog",
        "tags": ["projects", "ideas"]
    }
)
document = response.json()
print(f"Created document: {document}")

# Search documents
response = requests.get(
    f"{API_URL}/documents/search",
    params={"api_key": API_KEY, "query": "task manager"}
)
results = response.json()
print(f"Search results: {results}")
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

The API maintains three log files:
- `api.log`: API request/response logs
- `flashcards.log`: Flashcard database operation logs
- `documents_api.log`: Document API operation logs

## Backup and Restore

The API provides endpoints and a command-line script to backup and restore both flashcards and documents.

### API Endpoints

#### Download Cards/Documents
```
GET /download_cards?api_key=your-api-key-here
GET /documents/download?api_key=your-api-key-here
```
Downloads all cards or documents from the database.

#### Upload Cards/Documents
```
POST /upload_cards?api_key=your-api-key-here
POST /documents/upload?api_key=your-api-key-here

Body for cards:
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

Body for documents:
{
    "documents": [
        {
            "id": 1,
            "title": "Meeting Notes",
            "content": "# Meeting Notes\n\nDiscussion points...",
            "tags": ["meetings", "notes"],
            "created_at": "2025-02-09T00:00:00.000000",
            "updated_at": "2025-02-09T00:00:00.000000"
        },
        ...
    ]
}
```
Uploads data to the database. Existing items (matched by ID) will be updated, and new items will be inserted.

### Command-Line Script

A Python script is provided in the `scripts` directory to easily backup and restore your data:

Download all data to files:
```bash
python scripts/manage_data.py cards download cards_backup.json --api-key your-api-key-here
python scripts/manage_data.py documents download documents_backup.json --api-key your-api-key-here
```

Upload data from backup files:
```bash
python scripts/manage_data.py cards upload cards_backup.json --api-key your-api-key-here
python scripts/manage_data.py documents upload documents_backup.json --api-key your-api-key-here
```

The backup files include timestamps and all data in JSON format. This is useful for:
- Creating backups before server migrations
- Transferring data between instances
- Keeping local backups of your data