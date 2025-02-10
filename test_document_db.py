from document_db import DocumentDB
import logging
import os
from sqlalchemy.exc import SQLAlchemyError

def setup_test_db():
    """Set up a fresh test database"""
    db_path = "test_flashcards.db"
    if os.path.exists(db_path):
        try:
            os.remove(db_path)
        except PermissionError:
            # If file is locked, use a different name
            db_path = "test_flashcards_new.db"
    return DocumentDB(f'sqlite:///{db_path}')

def test_database_operations():
    """Test all document database operations"""
    # Initialize database with SQLite for testing
    db = setup_test_db()
    try:
        # Test creating a document
        doc_id = db.create_document(
            title="Python Programming",
            content="Python is a versatile programming language...",
            tags=["programming", "python"]
        )
        print(f"Created document with ID: {doc_id}")
        
        # Test retrieving the document
        doc = db.get_document("Python Programming")
        if doc is None:
            raise AssertionError("Failed to retrieve created document")
        if doc['title'] != "Python Programming":
            raise AssertionError("Retrieved document has incorrect title")
        if "programming" not in doc['tags']:
            raise AssertionError("Retrieved document missing expected tag")
        print(f"Retrieved document: {doc}")
        
        # Test getting all titles
        titles = db.get_all_titles()
        if "Python Programming" not in titles:
            raise AssertionError("Created document title not found in all titles")
        print(f"All titles: {titles}")
        
        # Test getting titles by tags
        tagged_titles = db.get_titles_by_tags(["programming"])
        if "Python Programming" not in tagged_titles:
            raise AssertionError("Document not found when filtering by tag")
        print(f"Titles with 'programming' tag: {tagged_titles}")
        
        # Test getting documents by tags
        tagged_docs = db.get_documents_by_tags(["programming"])
        if len(tagged_docs) == 0:
            raise AssertionError("No documents found with tag")
        if tagged_docs[0]['title'] != "Python Programming":
            raise AssertionError("Retrieved document has incorrect title")
        print(f"Documents with 'programming' tag: {tagged_docs}")
        
        # Test searching documents
        search_results = db.search_documents("versatile")
        if "Python Programming" not in search_results:
            raise AssertionError("Document not found in search results")
        print(f"Search results for 'versatile': {search_results}")
        
        # Test updating the document
        updated = db.update_document(
            title="Python Programming",
            content="Python is an amazing programming language...",
            tags=["programming", "python", "coding"]
        )
        if not updated:
            raise AssertionError("Failed to update document")
        print("Document updated successfully")
        
        # Test retrieving updated document
        updated_doc = db.get_document("Python Programming")
        if "coding" not in updated_doc['tags']:
            raise AssertionError("Updated tags not found in document")
        if "amazing" not in updated_doc['content']:
            raise AssertionError("Updated content not found in document")
        print(f"Retrieved updated document: {updated_doc}")
        
        # Test deleting the document
        deleted = db.delete_document("Python Programming")
        if not deleted:
            raise AssertionError("Failed to delete document")
        print("Document deleted successfully")
        
        # Verify deletion
        deleted_doc = db.get_document("Python Programming")
        if deleted_doc is not None:
            raise AssertionError("Document still exists after deletion")
        print("Verified document deletion")
    except Exception as e:
        print(f"Test failed: {str(e)}")
        raise
    finally:
        if os.path.exists("test_flashcards.db"):
            try:
                os.remove("test_flashcards.db")
            except PermissionError:
                pass

def test_error_handling():
    """Test error handling in database operations"""
    db = setup_test_db()
    try:
        # Test duplicate title
        doc_id = db.create_document(
            title="Test Document",
            content="Test content",
            tags=["test"]
        )
        
        try:
            db.create_document(
                title="Test Document",  # Same title should raise error
                content="Different content",
                tags=["test"]
            )
            raise AssertionError("Should have raised SQLAlchemyError for duplicate title")
        except SQLAlchemyError:
            print("Duplicate title test passed")
        
        # Test invalid updates
        if db.update_document("NonexistentDoc"):
            raise AssertionError("Update should fail for nonexistent document")
        print("Invalid update test passed")
        
        # Test invalid deletions
        if db.delete_document("NonexistentDoc"):
            raise AssertionError("Delete should fail for nonexistent document")
        print("Invalid deletion test passed")
    except Exception as e:
        print(f"Test failed: {str(e)}")
        raise
    finally:
        if os.path.exists("test_flashcards.db"):
            try:
                os.remove("test_flashcards.db")
            except PermissionError:
                pass

if __name__ == "__main__":
    # Set up console logging for test output
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    console_handler.setFormatter(formatter)
    logging.getLogger('documents').addHandler(console_handler)
    
    try:
        test_database_operations()
        test_error_handling()
        print("\nAll database tests completed successfully!")
    except Exception as e:
        print(f"\nTests failed with error: {str(e)}")
        raise