import os
import json
import boto3
import requests

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

sns_client = boto3.client('sns', 
    region_name=os.getenv('AWS_DEFAULT_REGION', 'us-east-1'),
    aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID', 'test'),
    aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY', 'test')
)

TELEGRAM_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

def send_telegram_message(payload):
    chat_id = payload.get('user_id')
    if not chat_id:
        chat_id = TELEGRAM_CHAT_ID
    if not TELEGRAM_TOKEN or not chat_id:
        print("Telegram: Skip sending, TELEGRAM_BOT_TOKEN or TELEGRAM_CHAT_ID missing.")
        return
        
    job = payload['job']
    title = job.get('title', 'New Job')
    company = job.get('company', 'Company')
    url = job.get('url', '')
    
    text = f"🚀 *New Match Found!*\n\n*{title}* @ {company}\n_Posted just now_\n\n[Apply Here]({url})"
    
    tg_url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    try:
        requests.post(tg_url, json={
            "chat_id": chat_id,
            "text": text,
            "parse_mode": "Markdown"
        })
        print("Telegram: Message sent successfully!")
    except Exception as e:
        print(f"Telegram: Failed to send message: {e}")

def trigger_local_websocket(payload):
    # This hits the local Flask server to emit the SocketIO event
    try:
        requests.post("http://127.0.0.1:5000/api/internal/emit-notification", json=payload)
    except Exception as e:
        print(f"Local WebSocket emit failed: {e}")

def publish_to_sns(payload):
    print(f"SNS: Publishing notification for user {payload['user_id']}")
    try:
        response = sns_client.publish(
            TopicArn="arn:aws:sns:us-east-1:123456789012:jobpulse-notifications", # Mock ARN
            Message=json.dumps(payload)
        )
        print("SNS Publish Response:", response)
    except Exception as e:
        print(f"SNS Publish failed (expected locally): {e}")
        
    # Local Dev Hackathon Fallback: Trigger Telegram and WebSocket directly
    send_telegram_message(payload)
    trigger_local_websocket(payload)



