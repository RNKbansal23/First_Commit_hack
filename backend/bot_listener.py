import os
import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from dotenv import load_dotenv
import boto3
from datetime import datetime

# Clear any fake AWS credentials that might be stuck in your terminal session's memory
os.environ.pop('AWS_ACCESS_KEY_ID', None)
os.environ.pop('AWS_SECRET_ACCESS_KEY', None)
os.environ.pop('AWS_SESSION_TOKEN', None)

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

COMPANY_LIST = ['Spotify', 'Meesho', 'Zomato', 'Lyft', 'Reddit', 'Airbnb', 'Stripe', 'Figma', 'Discord', 'GitLab', 'Pinterest', 'Twitch', 'Dropbox']

@bot.message_handler(commands=['start'])
def send_welcome(message):
    chat_id = message.chat.id
    user_states[chat_id] = {'step': 'keywords', 'companies': []}
    
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
        InlineKeyboardButton("India", callback_data="loc_india"),
        InlineKeyboardButton("United States", callback_data="loc_us"),
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
    
    loc_val = call.data.replace('loc_', '')
    if loc_val == 'us': loc_val = 'united states'
    
    user_states[chat_id]['work_mode'] = loc_val
    user_states[chat_id]['step'] = 'companies'
    
    markup = build_company_keyboard(user_states[chat_id]['companies'])
    
    bot.edit_message_text(
        chat_id=chat_id,
        message_id=call.message.message_id,
        text=f"Location set. Now, select the companies you want to watch (or select none for ALL companies):",
        reply_markup=markup
    )

def build_company_keyboard(selected_companies):
    markup = InlineKeyboardMarkup()
    markup.row_width = 2
    buttons = []
    for company in COMPANY_LIST:
        prefix = "✅ " if company in selected_companies else "⬜ "
        buttons.append(InlineKeyboardButton(f"{prefix}{company}", callback_data=f"comp_{company}"))
    markup.add(*buttons)
    markup.add(InlineKeyboardButton("✅ Finish & Save", callback_data="comp_submit"))
    return markup

@bot.callback_query_handler(func=lambda call: call.data.startswith('comp_'))
def process_company(call):
    chat_id = call.message.chat.id
    if user_states.get(chat_id, {}).get('step') != 'companies':
        bot.answer_callback_query(call.id, 'This button is expired!')
        return
        
    action = call.data.replace('comp_', '')
    
    if action == 'submit':
        finalize_setup(call)
    else:
        # Toggle company selection
        selected = user_states[chat_id]['companies']
        if action in selected:
            selected.remove(action)
        else:
            selected.append(action)
            
        markup = build_company_keyboard(selected)
        bot.edit_message_reply_markup(
            chat_id=chat_id,
            message_id=call.message.message_id,
            reply_markup=markup
        )

def finalize_setup(call):
    chat_id = call.message.chat.id
    state = user_states[chat_id]
    
    keywords = state.get('keywords', '')
    exp = state.get('experience_max', 5)
    loc_val = state.get('work_mode', 'any')
    companies = state.get('companies', [])
    
    try:
        # Save to DynamoDB
        watch_rules_table.put_item(
            Item={
                'id': f"wr_{chat_id}",
                'user_id': str(chat_id),
                'title_keywords': keywords,
                'experience_max': exp,
                'work_mode': loc_val,
                'companies': companies,
                'created_at': datetime.utcnow().isoformat()
            }
        )
        
        del user_states[chat_id]
        
        comps_text = ", ".join(companies) if companies else "All Companies"
        bot.edit_message_text(
            chat_id=chat_id,
            message_id=call.message.message_id,
            text=f"Setup Complete!\n\nRoles: {keywords}\nMax Exp: {exp} years\nLocation: {loc_val.title()}\nCompanies: {comps_text}\n\nI will now notify you instantly when matching jobs drop from AWS!"
        )
        
        # Immediate Database Scan for live data feedback
        bot.send_message(chat_id, "Searching the live AWS database for existing matches... 🔎")
        
        jobs_table = dynamodb.Table('FirstMover-Jobs')
        db_response = jobs_table.scan()
        all_jobs = db_response.get('Items', [])
        
        matching_jobs = []
        for job in all_jobs:
            if companies and job.get('company') not in companies:
                continue
                
            job_combined = (job.get('title', '') + " " + (job.get('description', '') or '')).lower()
            keyword_match = False
            kws = keywords.split(',') if keywords else []
            if not kws:
                keyword_match = True
            else:
                for kw in kws:
                    if kw.strip() and kw.strip().lower() in job_combined:
                        keyword_match = True
                        break
                        
            mode_match = True
            if loc_val and loc_val != 'any':
                job_loc = (job.get('location') or '').lower()
                job_mode = (job.get('work_mode') or '').lower()
                if loc_val not in job_mode and loc_val not in job_loc:
                    mode_match = False
                    
            if keyword_match and mode_match:
                matching_jobs.append(job)
                if len(matching_jobs) >= 3:
                    break
                    
        if not matching_jobs:
            markup = telebot.types.InlineKeyboardMarkup()
            markup.add(telebot.types.InlineKeyboardButton("Restart Setup 🔄", callback_data="restart_setup"))
            bot.send_message(
                chat_id, 
                "⚠️ **No Existing Matches Found**\n\nI checked the live database, but there are no current jobs that match these exact filters.\n\nDon't worry! I will stay on high alert and notify you the moment a new matching job drops on AWS. If you'd like to broaden your search right now, click below to try different filters.",
                parse_mode="Markdown",
                reply_markup=markup
            )
        else:
            bot.send_message(chat_id, f"🎉 Good news! I found **{len(matching_jobs)}** jobs currently active in the database! Here they are:", parse_mode="Markdown")
            for job in matching_jobs:
                title = job.get('title', 'New Job')
                company = job.get('company', 'Company')
                url = job.get('url', '')
                text = f"🚀 *{title}* @ {company}\n[Apply Here]({url})"
                bot.send_message(chat_id, text, parse_mode="Markdown", disable_web_page_preview=True)
                
    except Exception as e:
        print(f"DynamoDB Error: {e}")
        bot.send_message(chat_id, "Sorry, there was an error saving your preferences to the cloud.")


@bot.callback_query_handler(func=lambda call: call.data == "restart_setup")
def process_restart(call):
    bot.send_message(call.message.chat.id, "Let's set up your personalized job filter. What roles are you looking for?\n\n(e.g., frontend, backend, analyst, python, intern)")
    bot.register_next_step_handler(call.message, process_keywords_step)

if __name__ == '__main__':
    print("Bot Listener is running. Connected to AWS DynamoDB.")
    bot.infinity_polling()

