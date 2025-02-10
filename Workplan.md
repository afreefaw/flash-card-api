# Text Knowledge Base API

Currently I have a flashcards api. I want to add an api that can create, read, update, and delete text entries to a postgreSQL database. This will be a separate system to avoid impacting the flashcard functionality.

Each db entry is basically a text document with:
- title (unique identifier)
- tags (for organization/filtering)
- content (markdown formatted text)

The endpoints will be:
- get all titles
- get all titles based on tags
- get all documents based on tags
- get document based on title
- simple keyword search over document text and get titles
- create document
- update document (title or content or tags) based on title (overwrite)
- delete document based on title

One of the key aims is to be able to keep track of knowledge by sending things to this api (it will be handled by chatGPT actions). For example, creating an entry for someone I meet to track their kids' names, or taking down concepts I'm thinking about.

# Work Plan: Text Knowledge Base API

## Phase 1: Database Layer
📌 **Goal:** Set up PostgreSQL database and implement core document storage functionality.

### Tasks:

1. **Database Setup & Models** (Task 1)
   - Create new database schema for documents:
     ```sql
     CREATE TABLE documents (
       id SERIAL PRIMARY KEY,
       title TEXT UNIQUE NOT NULL,
       tags JSONB NOT NULL DEFAULT '[]',
       content TEXT NOT NULL,
       created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
       updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
     );
     ```
   - Implement DocumentDB class with SQLAlchemy:
     - Basic CRUD operations
     - Tag-based queries
     - Full-text search functionality
   - Add comprehensive error handling
   - Set up logging similar to flashcards.log

2. **Database Tests** (Task 2)
   - Create TestDocumentDB class following current testing style
   - Test cases:
     - Document creation with validation
     - Document retrieval (by title, tags)
     - Update operations
     - Delete operations
     - Tag filtering
     - Text search
   - Error case handling
   - Use pytest fixtures for database setup/teardown

## Phase 2: API Implementation
📌 **Goal:** Create REST API endpoints while maintaining separation from flashcard functionality.

### Tasks:

1. **Core API Setup** (Task 3)
   - Create DocumentAPI class as a separate FastAPI sub-application
   - Mount document API under /documents/ prefix in main app
   - Reuse existing API key authentication
   - Set up logging (documents_api.log)

2. **API Endpoints Implementation** (Task 4)
   - Implement routes:
     ```
     GET    /documents/titles
     GET    /documents/titles?tags=tag1,tag2
     GET    /documents?tags=tag1,tag2
     GET    /documents/{title}
     GET    /documents/search?query=keyword
     POST   /documents
     PUT    /documents/{title}
     DELETE /documents/{title}
     ```
   - Add request/response validation
   - Implement error handling

3. **API Testing** (Task 5)
   - Create TestDocumentAPI class following current style
   - Test all endpoints:
     - Authentication
     - CRUD operations
     - Tag filtering
     - Search functionality
   - Error cases and edge cases
   - Integration tests

## Phase 3: Documentation & Integration
📌 **Goal:** Ensure proper documentation and smooth integration.

### Tasks:

1. **Documentation Update** (Task 6)
   - Add new section to README.md
   - Document all endpoints with examples
   - Update environment setup instructions
   - Add example usage in Python

2. **Backup/Restore Support** (Task 7)
   - Add document backup endpoints
   - Update manage_cards.py to handle documents
   - Test backup/restore functionality

Each task is discrete and manageable, following the current project's implementation patterns while keeping the text knowledge base separate from the flashcard system. The existing API key authentication and database connection handling will be reused, but all new functionality will be isolated to avoid impacting the flashcard features.

---

### Implementation Notes:
- Maintains same testing style as current project
- Reuses authentication system
- Keeps separate database table
- Follows existing logging patterns
- Preserves current API endpoints
- Runs in same process as flashcard API
- Maintains code separation through FastAPI sub-applications
