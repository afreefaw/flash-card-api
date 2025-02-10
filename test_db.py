from db import FlashcardsDB
import logging

def test_database_operations():
    # Initialize database
    db = FlashcardsDB('test_flashcards.db')
    
    # Test creating a card
    card_id = db.create_card(
        question="What is the capital of France?",
        answer="Paris",
        tags=["geography", "europe"]
    )
    print(f"Created card with ID: {card_id}")
    
    # Test retrieving the card
    card = db.get_card(card_id)
    print(f"Retrieved card: {card}")
    
    # Test updating the card
    updated = db.update_card(
        card_id,
        question="What is the capital of France? (Updated)",
        tags=["geography", "europe", "capitals"]
    )
    print(f"Card update success: {updated}")
    
    # Test retrieving updated card
    updated_card = db.get_card(card_id)
    print(f"Retrieved updated card: {updated_card}")
    
    # Test last card tracking
    db.set_last_card(card_id)
    last_card_id = db.get_last_card()
    print(f"Last card ID: {last_card_id}")

if __name__ == "__main__":
    # Set up console logging for test output
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    console_handler.setFormatter(formatter)
    logging.getLogger('flashcards').addHandler(console_handler)
    
    try:
        test_database_operations()
        print("\nAll tests completed successfully!")
    except Exception as e:
        print(f"\nTest failed with error: {str(e)}")