import urllib.request
import json

def test_greenhouse(board):
    try:
        url = f"https://boards-api.greenhouse.io/v1/boards/{board}/jobs"
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=5) as response:
            data = json.loads(response.read().decode())
            print(f"Greenhouse {board}: {len(data.get('jobs', []))} jobs")
            return True
    except Exception as e:
        print(f"Greenhouse {board}: {e}")
        return False

def test_lever(board):
    try:
        url = f"https://api.lever.co/v0/postings/{board}?mode=json"
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=5) as response:
            data = json.loads(response.read().decode())
            print(f"Lever {board}: {len(data)} jobs")
            return True
    except Exception as e:
        print(f"Lever {board}: {e}")
        return False

print("Testing Greenhouse...")
for b in ["figma", "stripe", "openai", "airbnb", "pinterest", "reddit", "lyft", "twitch", "dropbox", "gitlab", "discord"]:
    test_greenhouse(b)

print("Testing Lever...")
for b in ["spotify", "meesho", "netflix", "yelp", "canva", "quora", "coursera", "udacity"]:
    test_lever(b)

