"""Quick endpoint verification for ACI system."""
import urllib.request, json, time

def req(label, url, method='GET', body=None):
    try:
        data = json.dumps(body).encode() if body else None
        r = urllib.request.Request(url, data=data,
            headers={'Content-Type': 'application/json'} if data else {})
        r.get_method = lambda: method
        resp = urllib.request.urlopen(r, timeout=8)
        return json.loads(resp.read()), resp.status
    except Exception as e:
        return None, str(e)

time.sleep(0.5)

# Homepage
d, s = req('Home', 'http://localhost:8000/')
print('HOME:', s)

# Create session
d, s = req('Create Session', 'http://localhost:8000/api/sessions',
    'POST', {'model_name': 'VerifyBot', 'model_version': '1.0'})
uid = d.get('session_uid') if d else None
print('CREATE SESSION:', s, '-', uid[:8] if uid else 'FAILED')

# Generate questions
d, s = req('Generate Qs', 'http://localhost:8000/api/questions/generate',
    'POST', {'mode': 'all'})
total = d.get('total') if d else 0
print('GENERATE QUESTIONS:', s, '-', total, 'questions')

# Save answers
if uid and total:
    d, s = req('Save Answers', 'http://localhost:8000/api/answers/save',
        'POST', {
            'session_uid': uid,
            'answers': {'1': 'This is a test answer.', '2': 'Another test answer.'},
            'question_ids': [1, 2]
        })
    saved = d.get('saved') if d else 0
    print('SAVE ANSWERS:', s, '-', saved, 'saved')

# Sessions list
d, s = req('Sessions List', 'http://localhost:8000/api/sessions')
count = len(d.get('sessions', [])) if d else 0
print('SESSIONS LIST:', s, '-', count, 'sessions')

# Status
d, s = req('Status', 'http://localhost:8000/api/status')
models = list(d.get('models', {}).keys()) if d else []
print('STATUS:', s, '-', len(models), 'models tracked')

print()
print('All checks complete.')
