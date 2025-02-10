import requests
from datetime import datetime, timedelta
import time
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class SpacedRepetitionTest:
    def __init__(self, base_url: str = "http://localhost:8000", api_key: str = None):
        if api_key is None:
            api_key = os.getenv("API_KEY", "your-secret-key-here")
        self.base_url = base_url
        self.api_key = api_key
    
    def create_test_card(self, question: str, answer: str, tags: list[str]) -> dict:
        """Helper to create a test card"""
        response = requests.post(
            f"{self.base_url}/create_card",
            params={"api_key": self.api_key},
            json={
                "question": question,
                "answer": answer,
                "tags": tags
            }
        )
        response.raise_for_status()
        return response.json()

    def get_card(self, card_id: int) -> dict:
        """Helper to get a specific card"""
        response = requests.get(
            f"{self.base_url}/next_card",
            params={"api_key": self.api_key}
        )
        response.raise_for_status()
        cards = []
        while response.status_code == 200:
            card = response.json()
            if card["id"] == card_id:
                return card
            cards.append(card)
            
            # Move this card to the future
            future_date = (datetime.utcnow() + timedelta(days=365)).isoformat()
            requests.post(
                f"{self.base_url}/set_due_date/{card['id']}",
                params={"api_key": self.api_key},
                json={"due_date": future_date}
            )
            response = requests.get(
                f"{self.base_url}/next_card",
                params={"api_key": self.api_key}
            )
        
        # Reset the cards we moved
        for card in cards:
            requests.post(
                f"{self.base_url}/set_due_date/{card['id']}",
                params={"api_key": self.api_key},
                json={"due_date": datetime.utcnow().isoformat()}
            )
        
        return None
    
    def test_next_card_retrieval(self):
        """Test getting the next due card"""
        logging.info("\nTesting next card retrieval...")
        
        # Create a test card
        card = self.create_test_card(
            "What is 2+2?",
            "4",
            ["math", "basic"]
        )
        logging.info(f"Created test card: {card}")
        
        # Set a future due date for any existing cards to ensure our new card is next
        response = requests.get(
            f"{self.base_url}/next_card",
            params={"api_key": self.api_key}
        )
        while response.status_code == 200:
            existing_card = response.json()
            if existing_card["id"] == card["id"]:
                break
                
            # Set due date to far future for existing card
            future_date = (datetime.utcnow() + timedelta(days=365)).isoformat()
            requests.post(
                f"{self.base_url}/set_due_date/{existing_card['id']}",
                params={"api_key": self.api_key},
                json={"due_date": future_date}
            )
            response = requests.get(
                f"{self.base_url}/next_card",
                params={"api_key": self.api_key}
            )
        
        # Get next card
        response = requests.get(
            f"{self.base_url}/next_card",
            params={"api_key": self.api_key}
        )
        response.raise_for_status()
        next_card = response.json()
        logging.info(f"Retrieved next card: {next_card}")
        
        # Verify it's our test card (should be, as it's due immediately)
        assert next_card["id"] == card["id"], "Retrieved card should match created card"
        
        return card["id"]
    
    def test_next_card_by_tag(self):
        """Test getting the next due card filtered by tag"""
        logging.info("\nTesting next card by tag retrieval...")
        
        # Create a test card with specific tag
        card = self.create_test_card(
            "What is the capital of France?",
            "Paris",
            ["geography", "europe"]
        )
        logging.info(f"Created test card with geography tag: {card}")
        
        # Set a future due date for any existing cards with the same tag
        response = requests.get(
            f"{self.base_url}/next_card_by_tag?tag=geography",
            params={"api_key": self.api_key}
        )
        while response.status_code == 200:
            existing_card = response.json()
            if existing_card["id"] == card["id"]:
                break
                
            # Set due date to far future for existing card
            future_date = (datetime.utcnow() + timedelta(days=365)).isoformat()
            requests.post(
                f"{self.base_url}/set_due_date/{existing_card['id']}",
                params={"api_key": self.api_key},
                json={"due_date": future_date}
            )
            response = requests.get(
                f"{self.base_url}/next_card_by_tag",
                params={"tag": "geography", "api_key": self.api_key}
            )
        
        # Get next card by tag
        response = requests.get(
            f"{self.base_url}/next_card_by_tag",
            params={"tag": "geography", "api_key": self.api_key}
        )
        response.raise_for_status()
        next_card = response.json()
        logging.info(f"Retrieved next card by tag 'geography': {next_card}")
        
        # Verify it's our test card
        assert next_card["id"] == card["id"], "Retrieved card should match created card"
        assert "geography" in next_card["tags"], "Retrieved card should have the requested tag"
    
    def test_success_progression(self, card_id: int):
        """Test the spaced repetition progression for successful reviews"""
        logging.info("\nTesting success progression...")
        
        # Get initial card state
        card = self.get_card(card_id)
        if not card:
            raise Exception(f"Could not find card {card_id}")
        
        last_due_date = datetime.fromisoformat(card['due_date'])
        logging.info(f"Initial card state: {card}")
        
        # Mark success multiple times and check due dates
        for i in range(3):
            # Mark as success
            response = requests.post(
                f"{self.base_url}/mark_success/{card_id}",
                params={"api_key": self.api_key}
            )
            response.raise_for_status()
            logging.info(f"Marked card {card_id} as success")
            
            # Get updated card state
            card = self.get_card(card_id)
            if not card:
                raise Exception(f"Could not find card {card_id} after marking success")
            
            current_due_date = datetime.fromisoformat(card['due_date'])
            logging.info(f"Card after success {i+1}: {card}")
            logging.info(f"New due date: {card['due_date']}")
            
            # Verify due date increased
            assert current_due_date > last_due_date, f"Due date should increase with each success (was {last_due_date}, now {current_due_date})"
            last_due_date = current_due_date
    
    def test_failure_reset(self):
        """Test resetting progress on failure"""
        logging.info("\nTesting failure reset...")
        
        # Create and progress a card
        card = self.create_test_card(
            "What is 5x5?",
            "25",
            ["math", "multiplication"]
        )
        card_id = card["id"]
        logging.info(f"Created test card: {card}")
        
        # Mark as success twice to progress intervals
        for _ in range(2):
            requests.post(
                f"{self.base_url}/mark_success/{card_id}",
                params={"api_key": self.api_key}
            )
        logging.info("Marked card as success twice")
        
        # Get card state before failure
        card_before = self.get_card(card_id)
        logging.info(f"Card before failure: {card_before}")
        
        # Now mark as failure
        response = requests.post(
            f"{self.base_url}/mark_failure/{card_id}",
            params={"api_key": self.api_key}
        )
        response.raise_for_status()
        logging.info("Marked card as failure")
        
        # Get card and verify reset
        card_after = self.get_card(card_id)
        logging.info(f"Card after failure: {card_after}")
        assert card_after["success_count"] == 0, "Success count should be reset to 0"
        assert datetime.fromisoformat(card_after["due_date"]) < datetime.fromisoformat(card_before["due_date"]), "Due date should be earlier after failure"
    
    def test_manual_due_date(self):
        """Test manually setting a due date"""
        logging.info("\nTesting manual due date setting...")
        
        # Create a test card
        card = self.create_test_card(
            "What is the speed of light?",
            "299,792,458 meters per second",
            ["physics", "science"]
        )
        card_id = card["id"]
        logging.info(f"Created test card: {card}")
        
        # Set due date to tomorrow
        tomorrow = (datetime.utcnow() + timedelta(days=1)).isoformat()
        response = requests.post(
            f"{self.base_url}/set_due_date/{card_id}",
            params={"api_key": self.api_key},
            json={"due_date": tomorrow}
        )
        response.raise_for_status()
        logging.info(f"Set due date to: {tomorrow}")
        
        # Try to get next card (should not get this card as it's due tomorrow)
        response = requests.get(
            f"{self.base_url}/next_card",
            params={"api_key": self.api_key}
        )
        if response.status_code == 404:
            logging.info("No cards due (expected as we set due date to tomorrow)")
        else:
            next_card = response.json()
            assert next_card["id"] != card_id, "Should not get card that's due tomorrow"

def run_tests():
    tester = SpacedRepetitionTest()
    
    try:
        # Run core functionality tests
        card_id = tester.test_next_card_retrieval()
        tester.test_next_card_by_tag()
        tester.test_success_progression(card_id)
        tester.test_failure_reset()
        tester.test_manual_due_date()
        
        print("\nAll spaced repetition tests completed successfully!")
    except Exception as e:
        print(f"\nTest failed: {str(e)}")
        raise

if __name__ == "__main__":
    print("Please ensure the API server is running before starting tests.")
    input("Press Enter to continue...")
    run_tests()