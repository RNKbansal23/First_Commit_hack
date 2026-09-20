import os
import json
import boto3
import requests

sns_client = boto3.client('sns', region_name=os.getenv('AWS_DEFAULT_REGION', 'us-east-1'))

TELEGRAM_TOKEN = "8853866585:AAGnS3G5IpOFa3n-ZbYJ94k38QW-rnLVyKE"

def send_telegram_message(payload):
    chat_id = payload.get('user_id')
    if not TELEGRAM_TOKEN or not chat_id:
        print("Telegram: Skip sending, TELEGRAM_BOT_TOKEN or chat_id missing.")
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
    pass

def publish_to_sns(payload):
    print(f"SNS: Publishing notification for user {payload['user_id']}")
    try:
        topic_arn = os.getenv('SNS_TOPIC_ARN')
        if topic_arn:
            sns_client.publish(
                TopicArn=topic_arn,
                Message=json.dumps(payload)
            )
    except Exception as e:
        print(f"SNS Publish failed (expected locally): {e}")
        
    # Local Dev Hackathon Fallback: Trigger Telegram directly
    send_telegram_message(payload)
