from flask import Flask, render_template, jsonify, request
from photos import fetch_photos
from classifier import classify_photo
from google_auth import get_credentials
import threading

app = Flask(__name__)

scan_results = []
scan_status = {'running': False, 'progress': 0, 'total': 0}

@app.route('/')
def index():
    return render_template('review.html')

@app.route('/auth')
def auth():
    try:
        creds = get_credentials()
        if creds and creds.valid:
            return jsonify({'status': 'ok'})
        return jsonify({'status': 'failed'})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)})

@app.route('/scan', methods=['POST'])
def scan():
    global scan_results, scan_status

    try:
        creds = get_credentials()
        if not creds or not creds.valid:
            return jsonify({'status': 'auth_required'})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)})

    scan_results = []
    scan_status = {'running': True, 'progress': 0, 'total': 0}

    def run_scan():
        global scan_results, scan_status
        try:
            photos = fetch_photos(max_photos=50)
            scan_status['total'] = len(photos)

            for i, photo in enumerate(photos):
                base_url = photo.get('baseUrl', '')
                decision = classify_photo(base_url)
                scan_results.append({
                    'id': photo['id'],
                    'url': base_url + '=w300-h300',
                    'filename': photo.get('filename', 'unknown'),
                    'decision': decision
                })
                scan_status['progress'] = i + 1

        except Exception as e:
            print(f"Scan error: {e}")
        finally:
            scan_status['running'] = False

    thread = threading.Thread(target=run_scan)
    thread.daemon = True
    thread.start()
    return jsonify({'status': 'started'})

@app.route('/debug')
def debug():
    """Raw API call for diagnosing scope / auth problems."""
    import requests as req
    try:
        creds = get_credentials()
        from google.auth.transport.requests import Request
        if creds.expired and creds.refresh_token:
            creds.refresh(Request())
        headers = {'Authorization': f'Bearer {creds.token}'}
        res = req.get(
            'https://photoslibrary.googleapis.com/v1/mediaItems',
            headers=headers,
            params={'pageSize': 5},
            timeout=15
        ).json()
        return jsonify({
            'token_valid': creds.valid,
            'token_scopes': list(creds.scopes) if creds.scopes else 'unknown',
            'api_response': res
        })
    except Exception as e:
        return jsonify({'error': str(e)})

@app.route('/progress')
def progress():
    return jsonify(scan_status)

@app.route('/results')
def results():
    return jsonify(scan_results)

@app.route('/delete', methods=['POST'])
def delete():
    data = request.json or {}
    filenames = data.get('filenames', [])

    if not filenames:
        return jsonify({'status': 'error', 'message': 'No filenames provided'}), 400

    output_path = 'flagged_for_deletion.txt'
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(f"Photos flagged for manual deletion ({len(filenames)} total)\n")
        f.write("=" * 50 + "\n")
        f.write("Open Google Photos and manually delete these files:\n\n")
        for fname in filenames:
            f.write(f"  - {fname}\n")

    print(f"Saved {len(filenames)} filenames to {output_path}")
    return jsonify({'status': 'ok', 'count': len(filenames), 'file': output_path})

if __name__ == '__main__':
    print("Opening browser for Google login first...")
    get_credentials()
    print("Login successful! Starting server...")
    app.run(debug=False, port=5000)