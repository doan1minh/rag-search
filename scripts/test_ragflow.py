import requests
import os
import json
from dotenv import load_dotenv
load_dotenv()

base_url = os.getenv('RAGFLOW_BASE_URL')
api_key = os.getenv('RAGFLOW_API_KEY')

# List all datasets
url = f"{base_url}/api/v1/datasets"
headers = {'Authorization': f'Bearer {api_key}'}
response = requests.get(url, headers=headers, timeout=30)
data = response.json()

datasets = data.get('data', [])
print(f"=== Found {len(datasets)} datasets ===\n")

for d in datasets:
    ds_id = d.get('id')
    ds_name = d.get('name')
    doc_count = d.get('document_count', 0)
    chunk_count = d.get('chunk_count', 0)
    print(f"ID: {ds_id}")
    print(f"Name: {ds_name}")
    print(f"Docs: {doc_count} | Chunks: {chunk_count}")
    print("-" * 50)

# Test retrieval with first dataset that has documents
print("\n=== Testing retrieval ===")
for d in datasets:
    doc_count = d.get('document_count', 0)
    chunk_count = d.get('chunk_count', 0)
    if chunk_count > 0:
        ds_id = d.get('id')
        ds_name = d.get('name')
        print(f"\nTesting dataset: {ds_name} (ID: {ds_id})")
        
        url = f"{base_url}/api/v1/retrieval"
        headers = {'Authorization': f'Bearer {api_key}', 'Content-Type': 'application/json'}
        payload = {
            'question': 'khoang san',
            'top_k': 3,
            'similarity_threshold': 0.1,
            'dataset_ids': [ds_id]
        }
        response = requests.post(url, json=payload, headers=headers, timeout=30)
        result = response.json()
        
        if result.get('code') == 0:
            chunks = result.get('data', {}).get('chunks', [])
            total = result.get('data', {}).get('total', 0)
            print(f"Results: {len(chunks)} chunks (total: {total})")
            if chunks:
                print(f"First chunk preview: {chunks[0].get('content', '')[:150]}...")
        break
