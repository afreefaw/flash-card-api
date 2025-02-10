#!/usr/bin/env python3
import argparse
import json
import requests
from typing import Dict, List
from datetime import datetime
from pydantic import BaseModel

# Hardcoded URL for the production server
API_URL = "https://flash-card-api-5t7m.onrender.com"

# Models matching the API
class CardBase(BaseModel):
    question: str
    answer: str
    tags: List[str]

class CardResponse(CardBase):
    id: int
    success_count: int
    due_date: str

class BulkCardsUpload(BaseModel):
    cards: List[CardResponse]

def download_cards(api_key: str, output_file: str) -> None:
    """Download all cards from the API and save to a file."""
    try:
        response = requests.get(
            f"{API_URL}/download_cards",
            params={"api_key": api_key}
        )
        response.raise_for_status()
        
        cards = response.json()["cards"]
        
        # Add timestamp to the export
        export_data = {
            "exported_at": datetime.utcnow().isoformat(),
            "cards": cards
        }
        
        with open(output_file, 'w') as f:
            json.dump(export_data, f, indent=2)
        
        print(f"Successfully downloaded {len(cards)} cards to {output_file}")
    
    except requests.exceptions.RequestException as e:
        print(f"Error downloading cards: {str(e)}")
        if hasattr(e.response, 'text'):
            print(f"Response: {e.response.text}")
        exit(1)

def upload_cards(api_key: str, input_file: str) -> None:
    """Upload cards from a file to the API."""
    try:
        with open(input_file, 'r') as f:
            data = json.load(f)
        
        raw_cards = data.get("cards", [])
        if not raw_cards:
            print("No cards found in the input file")
            return
        
        # Convert raw dictionaries to CardResponse objects
        cards = [CardResponse(**card) for card in raw_cards]
        upload_data = BulkCardsUpload(cards=cards)
        
        response = requests.post(
            f"{API_URL}/upload_cards",
            params={"api_key": api_key},
            json=upload_data.dict()
        )
        response.raise_for_status()
        
        result = response.json()
        print(f"Successfully uploaded cards:")
        print(f"- Inserted: {result['inserted']}")
        print(f"- Updated: {result['updated']}")
    
    except FileNotFoundError:
        print(f"Error: File {input_file} not found")
        exit(1)
    except json.JSONDecodeError:
        print(f"Error: File {input_file} contains invalid JSON")
        exit(1)
    except requests.exceptions.RequestException as e:
        print(f"Error uploading cards: {str(e)}")
        if hasattr(e.response, 'text'):
            print(f"Response: {e.response.text}")
        exit(1)

def download_documents(api_key: str, output_file: str) -> None:
    """Download all documents from the API and save to a file."""
    try:
        response = requests.get(
            f"{API_URL}/documents/download",
            params={"api_key": api_key}
        )
        response.raise_for_status()
        
        documents = response.json()["documents"]
        
        # Add timestamp to the export
        export_data = {
            "exported_at": datetime.utcnow().isoformat(),
            "documents": documents
        }
        
        with open(output_file, 'w') as f:
            json.dump(export_data, f, indent=2)
        
        print(f"Successfully downloaded {len(documents)} documents to {output_file}")
    
    except requests.exceptions.RequestException as e:
        print(f"Error downloading documents: {str(e)}")
        if hasattr(e.response, 'text'):
            print(f"Response: {e.response.text}")
        exit(1)

def upload_documents(api_key: str, input_file: str) -> None:
    """Upload documents from a file to the API."""
    try:
        with open(input_file, 'r') as f:
            data = json.load(f)
        
        documents = data.get("documents", [])
        if not documents:
            print("No documents found in the input file")
            return
        
        response = requests.post(
            f"{API_URL}/documents/upload",
            params={"api_key": api_key},
            json={"documents": documents}
        )
        response.raise_for_status()
        
        result = response.json()
        print(f"Successfully uploaded documents:")
        print(f"- Inserted: {result['inserted']}")
        print(f"- Updated: {result['updated']}")
    
    except FileNotFoundError:
        print(f"Error: File {input_file} not found")
        exit(1)
    except json.JSONDecodeError:
        print(f"Error: File {input_file} contains invalid JSON")
        exit(1)
    except requests.exceptions.RequestException as e:
        print(f"Error uploading documents: {str(e)}")
        if hasattr(e.response, 'text'):
            print(f"Response: {e.response.text}")
        exit(1)

def main():
    parser = argparse.ArgumentParser(description="Manage flashcards and documents backup and restore")
    parser.add_argument('type', choices=['cards', 'documents'], 
                       help='Type of data to manage')
    parser.add_argument('action', choices=['download', 'upload'], 
                       help='Action to perform')
    parser.add_argument('file', help='File to read from or write to')
    parser.add_argument('--api-key', required=True,
                       help='API key for authentication')
    
    args = parser.parse_args()
    
    if args.type == 'cards':
        if args.action == 'download':
            download_cards(args.api_key, args.file)
        else:  # upload
            upload_cards(args.api_key, args.file)
    else:  # documents
        if args.action == 'download':
            download_documents(args.api_key, args.file)
        else:  # upload
            upload_documents(args.api_key, args.file)

if __name__ == "__main__":
    main()