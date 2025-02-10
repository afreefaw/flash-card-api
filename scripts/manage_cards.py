#!/usr/bin/env python3
import argparse
import json
import os
import requests
from typing import Dict, List
from datetime import datetime

def load_config() -> Dict[str, str]:
    """Load configuration from environment or .env file."""
    from dotenv import load_dotenv
    load_dotenv()
    
    api_key = os.getenv("API_KEY")
    api_url = os.getenv("API_URL", "http://localhost:8000")
    
    if not api_key:
        raise ValueError("API_KEY environment variable must be set")
    
    return {
        "api_key": api_key,
        "api_url": api_url.rstrip("/")
    }

def download_cards(config: Dict[str, str], output_file: str) -> None:
    """Download all cards from the API and save to a file."""
    try:
        response = requests.get(
            f"{config['api_url']}/download_cards",
            params={"api_key": config['api_key']}
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

def upload_cards(config: Dict[str, str], input_file: str) -> None:
    """Upload cards from a file to the API."""
    try:
        with open(input_file, 'r') as f:
            data = json.load(f)
        
        cards = data.get("cards", [])
        if not cards:
            print("No cards found in the input file")
            return
        
        response = requests.post(
            f"{config['api_url']}/upload_cards",
            params={"api_key": config['api_key']},
            json={"cards": cards}
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

def main():
    parser = argparse.ArgumentParser(description="Manage flashcards backup and restore")
    parser.add_argument('action', choices=['download', 'upload'], 
                       help='Action to perform')
    parser.add_argument('file', help='File to read from or write to')
    
    args = parser.parse_args()
    config = load_config()
    
    if args.action == 'download':
        download_cards(config, args.file)
    else:  # upload
        upload_cards(config, args.file)

if __name__ == "__main__":
    main()