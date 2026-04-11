import ollama
import requests
import base64
from PIL import Image
import io

def classify_photo(photo_url):
    try:
        # Download the image
        response = requests.get(photo_url + '=w400-h400', timeout=10)
        img_data = response.content

        # Convert to base64
        img_b64 = base64.b64encode(img_data).decode('utf-8')

        # Ask LLaVA to classify
        result = ollama.chat(
            model='llava',
            messages=[{
                'role': 'user',
                'content': '''Look at this image carefully. Classify it as exactly one of:
- KEEP: if it contains people, faces, selfies, family moments, documents, forms, papers, screenshots, readable text, receipts
- DELETE: if it contains construction sites, elevators, lift shafts, machinery, equipment, wires, empty rooms, walls, technical work

Reply with ONLY the word KEEP or DELETE, nothing else.''',
                'images': [img_b64]
            }]
        )

        decision = result['message']['content'].strip().upper()
        if 'KEEP' in decision:
            return 'KEEP'
        elif 'DELETE' in decision:
            return 'DELETE'
        else:
            return 'KEEP'  # Default to safe side

    except Exception as e:
        print(f"Classification error: {e}")
        return 'KEEP'  # Safe default