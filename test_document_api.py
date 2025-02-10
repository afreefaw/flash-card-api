import requests
import json
from typing import Optional, List, Dict, Any

class DocumentAPITest:
    def __init__(self, base_url: str = "http://localhost:8000", api_key: str = "your-secret-key-here"):
        self.base_url = f"{base_url}/documents"
        self.api_key = api_key
    
    def create_document(self, title: str, content: str, tags: List[str]) -> Optional[Dict[str, Any]]:
        """Test creating a new document"""
        try:
            response = requests.post(
                f"{self.base_url}",
                params={"api_key": self.api_key},
                json={
                    "title": title,
                    "content": content,
                    "tags": tags
                }
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Error creating document: {str(e)}")
            if hasattr(e.response, 'text'):
                print(f"Response: {e.response.text}")
            return None
    
    def update_document(self, title: str, content: Optional[str] = None, 
                       tags: Optional[List[str]] = None) -> Optional[Dict[str, Any]]:
        """Test updating an existing document"""
        update_data = {}
        if content is not None:
            update_data["content"] = content
        if tags is not None:
            update_data["tags"] = tags
        
        try:
            response = requests.put(
                f"{self.base_url}/{title}",
                params={"api_key": self.api_key},
                json=update_data
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Error updating document: {str(e)}")
            if hasattr(e.response, 'text'):
                print(f"Response: {e.response.text}")
            return None
    
    def get_document(self, title: str) -> Optional[Dict[str, Any]]:
        """Test retrieving a document"""
        try:
            response = requests.get(
                f"{self.base_url}/{title}",
                params={"api_key": self.api_key}
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Error getting document: {str(e)}")
            if hasattr(e.response, 'text'):
                print(f"Response: {e.response.text}")
            return None
    
    def get_titles(self) -> Optional[List[str]]:
        """Test retrieving all titles"""
        try:
            response = requests.get(
                f"{self.base_url}/titles",
                params={"api_key": self.api_key}
            )
            response.raise_for_status()
            return response.json()["titles"]
        except requests.exceptions.RequestException as e:
            print(f"Error getting titles: {str(e)}")
            if hasattr(e.response, 'text'):
                print(f"Response: {e.response.text}")
            return None
    
    def get_titles_by_tags(self, tags: List[str]) -> Optional[List[str]]:
        """Test retrieving titles filtered by tags"""
        try:
            response = requests.get(
                f"{self.base_url}/titles/by_tags",
                params={
                    "api_key": self.api_key,
                    "tags": ",".join(tags)
                }
            )
            response.raise_for_status()
            return response.json()["titles"]
        except requests.exceptions.RequestException as e:
            print(f"Error getting titles by tags: {str(e)}")
            if hasattr(e.response, 'text'):
                print(f"Response: {e.response.text}")
            return None
    
    def search_documents(self, query: str) -> Optional[List[str]]:
        """Test searching documents"""
        try:
            response = requests.get(
                f"{self.base_url}/search",
                params={
                    "api_key": self.api_key,
                    "query": query
                }
            )
            response.raise_for_status()
            return response.json()["titles"]
        except requests.exceptions.RequestException as e:
            print(f"Error searching documents: {str(e)}")
            if hasattr(e.response, 'text'):
                print(f"Response: {e.response.text}")
            return None
    
    def test_authentication(self) -> bool:
        """Test authentication with invalid API key"""
        try:
            response = requests.post(
                f"{self.base_url}",
                params={"api_key": "invalid-key"},
                json={
                    "title": "Test Document",
                    "content": "Test content",
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
    
    def delete_document(self, title: str) -> bool:
        """Test deleting a document"""
        try:
            response = requests.delete(
                f"{self.base_url}/{title}",
                params={"api_key": self.api_key}
            )
            response.raise_for_status()
            return True
        except requests.exceptions.RequestException as e:
            print(f"Error deleting document: {str(e)}")
            if hasattr(e.response, 'text'):
                print(f"Response: {e.response.text}")
            return False

def run_tests():
    print("Starting Document API tests...")
    api = DocumentAPITest()
    
    # Test authentication
    print("\nTesting authentication...")
    api.test_authentication()
    
    # Test document creation
    print("\nTesting document creation...")
    doc = api.create_document(
        title="Meeting with John",
        content="Met with John to discuss the project. His kids Tommy (5) and Sarah (7) were mentioned.",
        tags=["meetings", "contacts"]
    )
    if doc:
        print(f"Created document: {json.dumps(doc, indent=2)}")
        
        # Test document retrieval
        print("\nTesting document retrieval...")
        retrieved_doc = api.get_document(doc["title"])
        if retrieved_doc:
            print(f"Retrieved document: {json.dumps(retrieved_doc, indent=2)}")
        
        # Test document update
        print("\nTesting document update...")
        updated_doc = api.update_document(
            title=doc["title"],
            content="Updated meeting notes with John. Kids: Tommy (5) and Sarah (7).",
            tags=["meetings", "contacts", "updated"]
        )
        if updated_doc:
            print(f"Updated document: {json.dumps(updated_doc, indent=2)}")
        
        # Test tag filtering
        print("\nTesting tag filtering...")
        tagged_titles = api.get_titles_by_tags(["meetings"])
        if tagged_titles:
            print(f"Documents with 'meetings' tag: {tagged_titles}")
        
        # Test search
        print("\nTesting search...")
        search_results = api.search_documents("Tommy")
        if search_results:
            print(f"Search results for 'Tommy': {search_results}")
        
        # Test deletion
        print("\nTesting document deletion...")
        if api.delete_document(doc["title"]):
            print("Document deleted successfully")
            
            # Verify document is deleted by trying to retrieve it
            failed_retrieval = api.get_document(doc["title"])
            if not failed_retrieval:
                print("Verified document was deleted (retrieval failed as expected)")
    
    print("\nTests completed!")

if __name__ == "__main__":
    print("Please ensure the API server is running before starting tests.")
    input("Press Enter to continue...")
    run_tests()