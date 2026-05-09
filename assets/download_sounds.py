"""
assets/download_sounds.py
Downloads free CC0 table tennis sound effects from Freesound (via direct URLs).
Run once before starting the game: python assets/download_sounds.py

All sounds are CC0 / royalty-free for non-commercial use.
"""
import os
import urllib.request

SOUNDS_DIR = os.path.join(os.path.dirname(__file__), 'sounds')
os.makedirs(SOUNDS_DIR, exist_ok=True)

# Direct download URLs for CC0 sounds
# Using Wikimedia Commons and other open sources
SOUND_URLS = {
    # Crisp hit sound (wood knock)
    'pock.wav':
        'https://upload.wikimedia.org/wikipedia/commons/8/8e/Tap.ogg',
    # Ball bounce (hollow thud)
    'thud.wav':
        'https://upload.wikimedia.org/wikipedia/commons/a/a8/Bounce.ogg',
    # Crowd cheer
    'cheer.wav':
        'https://upload.wikimedia.org/wikipedia/commons/b/b9/Applause.ogg',
    # Ambient crowd noise
    'ambient.wav':
        'https://upload.wikimedia.org/wikipedia/commons/4/41/Crowd-noise.ogg',
}

# Fallback: generate minimal silent WAV files so the game won't crash
# if download fails or user is offline.
def _write_silent_wav(path, duration_s=0.05, sample_rate=22050):
    import struct, wave
    n = int(sample_rate * duration_s)
    with wave.open(path, 'w') as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sample_rate)
        wf.writeframes(struct.pack('<' + 'h'*n, *([0]*n)))


def download():
    for fname, url in SOUND_URLS.items():
        dest = os.path.join(SOUNDS_DIR, fname)
        if os.path.exists(dest) and os.path.getsize(dest) > 1000:
            print(f'  [skip] {fname} already exists.')
            continue
        print(f'  Downloading {fname} …', end=' ', flush=True)
        try:
            req = urllib.request.Request(url, headers={
                'User-Agent': 'Mozilla/5.0 TableTennisSoundDownloader/1.0'
            })
            with urllib.request.urlopen(req, timeout=15) as resp:
                data = resp.read()
            with open(dest, 'wb') as f:
                f.write(data)
            print(f'OK ({len(data)//1024} KB)')
        except Exception as e:
            print(f'FAILED ({e})')
            print(f'  -> Writing silent placeholder for {fname}')
            _write_silent_wav(dest)


if __name__ == '__main__':
    print('Downloading Table Tennis sound assets...')
    download()
    print('\nDone. Files saved to:', SOUNDS_DIR)
