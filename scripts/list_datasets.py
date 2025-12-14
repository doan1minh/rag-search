import requests
import os
import json
from dotenv import load_dotenv
load_dotenv()

base_url = os.getenv('RAGFLOW_BASE_URL')
api_key = os.getenv('RAGFLOW_API_KEY')

url = f"{base_url}/api/v1/datasets"
headers = {'Authorization': f'Bearer {api_key}'}
response = requests.get(url, headers=headers, timeout=30)
data = response.json()

datasets = data.get('data', [])
print(f"Found {len(datasets)} datasets:\n")

for d in datasets:
    print(f"ID: {d.get('id')}")
    print(f"Name: {d.get('name')}")
    print(f"Document count: {d.get('document_count', 0)}")
    print("-" * 40)
