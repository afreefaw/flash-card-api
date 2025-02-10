import requests
import json
from typing import Optional

class FlashcardsAPITest:
    def __init__(self, base_url: str = "http://localhost:8000", api_key: str = "your-secret-key-here"):
        self.base_url = base_url
        self.headers = {"X-API-Key": api_key}
    
    def create_card(self, question: str, answer: str, tags: list[str]) -> Optional[dict]:
        """Test creating a new card"""
        try:
            response = requests.post(
                f"{self.base_url}/create_card",
                headers=self.headers,
                json={
                    "question": question,
                    "answer": answer,
                    "tags": tags
                }
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Error creating card: {str(e)}")
            if hasattr(e.response, 'text'):
                print(f"Response: {e.response.text}")
            return None
    
    def update_card(self, card_id: int, question: Optional[str] = None, 
                   answer: Optional[str] = None, tags: Optional[list[str]] = None) -> Optional[dict]:
        """Test updating an existing card"""
        update_data = {}
        if question is not None:
            update_data["question"] = question
        if answer is not None:
            update_data["answer"] = answer
        if tags is not None:
            update_data["tags"] = tags
        
        try:
            response = requests.put(
                f"{self.base_url}/update_card/{card_id}",
                headers=self.headers,
                json=update_data
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Error updating card: {str(e)}")
            if hasattr(e.response, 'text'):
                print(f"Response: {e.response.text}")
            return None
    
    def test_authentication(self) -> bool:
        """Test authentication with invalid API key"""
        try:
            response = requests.post(
                f"{self.base_url}/create_card",
                headers={"X-API-Key": "invalid-key"},
                json={
                    "question": "Test question",
                    "answer": "Test answer",
                    "tags": ["test"]
                }
            )
            if response.status_code == 401:
                print("Authentication test passed: Invalid key correctly rejected")
                return True
            else:
                print(f"Authentication test failed: Expected 401, got {response.status_code}")
                return False
        except requests.exceptions.RequestException as e:
            print(f"Error testing authentication: {str(e)}")
            return False
    
    def delete_card(self, card_id: int) -> bool:
        """Test deleting a card"""
        try:
            response = requests.delete(
                f"{self.base_url}/delete_card/{card_id}",
                headers=self.headers
            )
            response.raise_for_status()
            return True
        except requests.exceptions.RequestException as e:
            print(f"Error deleting card: {str(e)}")
            if hasattr(e.response, 'text'):
                print(f"Response: {e.response.text}")
            return False

def run_tests():
    print("Starting API tests...")
    api = FlashcardsAPITest()
    
    # Test authentication
    print("\nTesting authentication...")
    api.test_authentication()
    
    # Test card creation
    print("\nTesting card creation...")
    card = api.create_card(
        question="What is the capital of Japan?",
        answer="Tokyo",
        tags=["geography", "asia"]
    )
    if card:
        print(f"Created card: {json.dumps(card, indent=2)}")
        
        # Test card update
        print("\nTesting card update...")
        updated_card = api.update_card(
            card_id=card["id"],
            question="What is the capital of Japan? (Updated)",
            tags=["geography", "asia", "capitals"]
        )
        if updated_card:
            print(f"Updated card: {json.dumps(updated_card, indent=2)}")
    
        # Test deletion
        print("\nTesting card deletion...")
        if api.delete_card(card["id"]):
            print("Card deleted successfully")
            
            # Verify card is deleted by trying to update it
            failed_update = api.update_card(
                card_id=card["id"],
                question="This should fail"
            )
            if not failed_update:
                print("Verified card was deleted (update failed as expected)")
    
    print("\nTests completed!")

if __name__ == "__main__":
    print("Please ensure the API server is running before starting tests.")
    input("Press Enter to continue...")
    run_tests()