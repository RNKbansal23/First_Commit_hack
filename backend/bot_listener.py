import os
import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from dotenv import load_dotenv
import boto3
from datetime import datetime

load_dotenv()

TELEGRAM_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
if not TELEGRAM_TOKEN:
    print("ERROR: TELEGRAM_BOT_TOKEN not found in .env")
    exit(1)

bot = telebot.TeleBot(TELEGRAM_TOKEN)
user_states = {}

# Initialize DynamoDB resource
dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
watch_rules_table = dynamodb.Table('FirstMover-WatchRules')

@bot.message_handler(commands=['start'])
def send_welcome(message):
    chat_id = message.chat.id
    user_states[chat_id] = {'step': 'keywords'}
    
    bot.send_message(
        chat_id,
        "Welcome to JobPulse!\n\n"
        "Let's set up your personalized job filter. "
        "What roles are you looking for? \n\n"
        "(e.g., frontend, backend, analyst, python, intern)",
    )

@bot.message_handler(func=lambda message: user_states.get(message.chat.id, {}).get('step') == 'keywords')
def process_keywords(message):
    chat_id = message.chat.id
    user_states[chat_id]['keywords'] = message.text
    user_states[chat_id]['step'] = 'experience'
    
    markup = InlineKeyboardMarkup()
    markup.row_width = 3
    markup.add(
        InlineKeyboardButton("0 (Fresher)", callback_data="exp_0"),
        InlineKeyboardButton("1-2 Years", callback_data="exp_2"),
        InlineKeyboardButton("3-5 Years", callback_data="exp_5"),
        InlineKeyboardButton("5+ Years", callback_data="exp_10")
    )
    
    bot.send_message(
        chat_id,
        "Great! What is your maximum years of experience?",
        reply_markup=markup
    )

@bot.callback_query_handler(func=lambda call: call.data.startswith('exp_'))
def process_experience(call):
    chat_id = call.message.chat.id
    if user_states.get(chat_id, {}).get('step') != 'experience':
        bot.answer_callback_query(call.id, 'This button is expired!')
        return
    exp_val = int(call.data.split('_')[1])
    
    user_states[chat_id]['experience_max'] = exp_val
    user_states[chat_id]['step'] = 'location'
    
    markup = InlineKeyboardMarkup()
    markup.row_width = 2
    markup.add(
        InlineKeyboardButton("Remote Only", callback_data="loc_remote"),
        InlineKeyboardButton("Anywhere", callback_data="loc_any")
    )
    
    bot.edit_message_text(
        chat_id=chat_id,
        message_id=call.message.message_id,
        text=f"Experience set to {exp_val} years. Any location preference?",
        reply_markup=markup
    )

@bot.callback_query_handler(func=lambda call: call.data.startswith('loc_'))
def process_location(call):
    chat_id = call.message.chat.id
    if user_states.get(chat_id, {}).get('step') != 'location':
        bot.answer_callback_query(call.id, 'This button is expired!')
        return
    
    loc_val = "remote" if call.data == "loc_remote" else "any"
    keywords = user_states[chat_id].get('keywords', '')
    exp = user_states[chat_id].get('experience_max', 5)
    
    try:
        # Save to DynamoDB
        watch_rules_table.put_item(
            Item={
                'id': f"wr_{chat_id}",
                'user_id': str(chat_id),
                'title_keywords': keywords,
                'experience_max': exp,
                'work_mode': loc_val,
                'created_at': datetime.utcnow().isoformat()
            }
        )
        
        del user_states[chat_id]
        
        mode_text = "Remote only" if loc_val == "remote" else "Any location"
        bot.edit_message_text(
            chat_id=chat_id,
            message_id=call.message.message_id,
            text=f"Setup Complete!\n\nRoles: {keywords}\nMax Exp: {exp} years\nLocation: {mode_text}\n\nI will now notify you instantly when matching jobs drop from AWS!"
        )
    except Exception as e:
        print(f"DynamoDB Error: {e}")
        bot.send_message(chat_id, "Sorry, there was an error saving your preferences to the cloud.")

if __name__ == '__main__':
    print("Bot Listener is running. Connected to AWS DynamoDB.")
    bot.infinity_polling()


