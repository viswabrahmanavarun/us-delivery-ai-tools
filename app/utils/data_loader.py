import json
import os
from pathlib import Path

def load_json(filepath):
    with open(filepath, 'r') as f:
        return json.load(f)

def load_tickets():
    base_path = Path(__file__).parent.parent.parent
    filepath = base_path / 'data' / 'tickets.json'
    return load_json(filepath)

def load_accounts():
    base_path = Path(__file__).parent.parent.parent
    filepath = base_path / 'data' / 'accounts.json'
    return load_json(filepath)

def load_knowledge_base():
    base_path = Path(__file__).parent.parent.parent
    kb_path = base_path / 'knowledge-base'
    
    docs = []
    for root, _, files in os.walk(kb_path):
        for file in files:
            if file.endswith('.md'):
                filepath = os.path.join(root, file)
                with open(filepath, 'r') as f:
                    docs.append({
                        "filename": file,
                        "path": os.path.relpath(filepath, base_path),
                        "content": f.read()
                    })
    return docs
