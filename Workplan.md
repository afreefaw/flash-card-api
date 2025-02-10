Overall concept:

Create a super simple spaced repetition flash card api. Cards are stored in an SQLite database.

The way to interact with it will be through customGPTs in chatGPT. I will host a custom api on my computer, expose it to the web, and then have my custom GPT send requests via tool use. (we can ignore the GPT integration for now, basically we just need to create the api service for now).

The api needs to have functionality to:
- create a new card
- update an existing card
- get next card (by due date - whichever is furthest in the past first. Fine to get things that are not due yet.)
- get next card that has a specific tag (by due date, same method as above) 
- mark last card received using either of the two previous methods for getting cards as a success or fail (which also updates the due date, see below))
- Set due date for last card received

cards need to have:
- question
- answer
- success_count (integer count)
- due_date (timestamp - not specified by the card creator, but rather updated on the backend)
- tags (can be multiple)

The due dates are based on the following logic, determined anytime a card is created or failed or succeeded on:
- the intervals (in days) are [1/48, 1, 3, 7, 14, 30, 120, 365] and then 365 ongoing
- when a card is created, it is due after the first interval has elapsed.
- after a success, the interval increases to the next one in that list
- after a failure, the interval resets to the beginning.

There should be a very simple authentication mechanism, just requiring a passkey.

Everything should persist between sessions (including tracking of last card) and be lightweight and simple.

There should be limited/concise but clear logging for debugging (not print statements).

**WORKPLAN STARTS HERE - has different chunks of work, to be handled one at a time.**

Implementation Plan: Spaced Repetition Flashcard API
Chunk 1: Database Schema, Storage System & Logging
Goal: Set up an SQLite database, implement basic CRUD operations, and add logging for debugging.

Tasks:

Database Schema Design:

Create an SQLite database with a cards table.
Define fields: id (primary key), question, answer, success_count, due_date, and tags (stored as JSON or in a separate table).
Create a metadata table to store last_card_id for tracking the last reviewed card.
Database Operations:

Implement functions to:
Create a new flashcard.
Update an existing flashcard.
Retrieve a flashcard by ID.
Store and retrieve session metadata (e.g., last card received).
Logging Integration:

Use Python’s logging module.
Log database queries, API requests, and errors.
Use different log levels (INFO, WARNING, ERROR).
Ensure logs persist to a file for debugging.
Persistence & Initialization:

Ensure the database persists between sessions.
Add a setup function to initialize the database if it doesn't exist.


**Chunk 2: API Endpoints & Authentication**
Goal: Expose API endpoints for interacting with flashcards, require authentication, and integrate logging for API requests.

Tasks:

API Framework:

Use Flask or FastAPI to serve the API.
Implement structured request handling and response formatting.
Authentication:

Require a passkey in headers for all requests.
Reject unauthorized requests with proper status codes.
Logging Enhancements:

Log incoming API requests and responses.
Log authentication failures.
Track execution time for requests (to identify slow queries).
API Endpoints:

POST /create_card → Create a new card.
PUT /update_card/{id} → Update an existing card.
GET /next_card → Retrieve the next due card.
GET /next_card_by_tag?tag=<tag> → Retrieve the next due card with a specific tag.


**Chunk 3: Review Logic & Due Date Calculation**
Goal: Implement spaced repetition logic with proper tracking and logging of state changes.

Tasks:

Determine the Next Due Card:

Sort by due_date (oldest first).
Retrieve the first available card.
Log the card selection process.
Update Due Dates & Track Reviews:

Implement /mark_success:
Increment success_count.
Set due_date based on the next interval.
Implement /mark_fail:
Reset success_count to 0.
Reset due_date to the first interval.
Log each state change for tracking.
Store & Retrieve Last Reviewed Card:

Track last_card_id in the metadata table.
Implement /set_due_date to manually override the due date for the last received card.
Log the last card updates.