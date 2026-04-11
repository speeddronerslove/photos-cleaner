import requests
from google_auth import get_credentials
from google.auth.transport.requests import Request

def fetch_photos(max_photos=100):
    creds = get_credentials()
    
    # Refresh token if needed
    if creds and creds.expired and creds.refresh_token:
        creds.refresh(Request())

    headers = {'Authorization': f'Bearer {creds.token}'}
    
    photos = []
    next_page = None

    while len(photos) < max_photos:
        params = {'pageSize': min(50, max_photos - len(photos))}
        if next_page:
            params['pageToken'] = next_page

        res = requests.get(
            'https://photoslibrary.googleapis.com/v1/mediaItems',
            headers=headers,
            params=params,
            timeout=30
        ).json()

        print("=== API Response ===")
        print(res)
        print("===================")

        if 'error' in res:
            err = res['error']
            print(f"API Error {err.get('code')}: {err.get('message')} [{err.get('status')}]")
            break

        items = res.get('mediaItems', [])
        if not items:
            print("No items in response (empty library page or end of results)")
            break
            
        photos.extend(items)
        print(f"Fetched {len(items)} items, total so far: {len(photos)}")
        
        next_page = res.get('nextPageToken')
        if not next_page:
            print("No more pages.")
            break

    print(f"Total photos fetched: {len(photos)}")
    return photos[:max_photos]