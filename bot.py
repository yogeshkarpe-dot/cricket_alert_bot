from urllib.request import urlopen
from bs4 import BeautifulSoup as soup
import logging
from telegram import Update
from telegram.ext import ApplicationBuilder,ContextTypes,CommandHandler
import asyncio
import json
import requests
import os


TOKEN = os.getenv("BOTAPIKEY")
application = ApplicationBuilder().token(TOKEN).build()
url = "http://static.cricinfo.com/rss/livescores.xml"
op = urlopen(url)
rd = op.read()
op.close()
data = soup(rd, 'xml')
matches_list_description = data.find_all('description')
match_id = data.find_all('guid')
match_list = []
match_id_list = []
match_list_str = ""
i = 0
over = ""

for match in matches_list_description:
    tmp = match.get_text()
    match_list.append(tmp)
    match_list_str += str(i)+". "+tmp+"\n"+"-"*50+"\n"
    i+=1

for id in match_id:
    match_id_list.append(id.get_text())

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

async def match_updates(match_url,chat_id,context):
    while True:
        telegram_url = f'https://api.telegram.org/bot6089051653:AAGTFhli1tk7FWWSNBYXtV7PeHH6Ed2a2I0/sendMessage'
        json_url = match_url.replace(".html", ".json")
        page = urlopen(json_url)
        json_data = json.load(page)
        status = json_data['live']['status']
        score = json_data['match']['current_summary_abbreviation']
        
        if status == "Match drawn" or status == "Match over":
            response = requests.post(telegram_url, json={'chat_id':chat_id, 'text':status})
            break

        elif "Match over" in score:
            response = requests.post(telegram_url, json={'chat_id':chat_id, 'text':status})
            break

        elif "Match delayed" in score or "Stumps" in score:
            response = requests.post(telegram_url, json={'chat_id':chat_id, 'text':score})
            response = requests.post(telegram_url, json={'chat_id':chat_id, 'text':status})
            break

        elif score == "":
            response = requests.post(telegram_url, json={'chat_id':chat_id, 'text':status})
            break
        elif "Innings break" in score:
            response = requests.post(telegram_url, json={'chat_id':chat_id, 'text':score})
            break
        else:
            mes_sent = False
            ball = json_data['comms'][0]['ball'][0]
            global over
            over_actual = ball['overs_actual']

            if over_actual != over:
                over = over_actual
                players = ball['players']
                event = ball['event']
                dismissal = ball['dismissal']
                    
                message = "overs "+over+" - "+ players+ ", "+ event +". "+ dismissal + "\nScore: "+score + ".\nStatus: "+status+"."

                if event == "FOUR" or event == "SIX" or "OUT" in event:
                    response = requests.post(telegram_url, json={'chat_id':chat_id, 'text':message})

            await asyncio.sleep(5)
    await asyncio.sleep(5)

async def stop(update=Update, context=ContextTypes.DEFAULT_TYPE):
    task = context.user_data.get('message_task')
    if task and not task.done():
        task.cancel()

        await context.bot.send_message(chat_id=update.effective_chat.id, text='match updates stopped.')

async def get_event(update=Update, context=ContextTypes.DEFAULT_TYPE,):
    chat_id = update.effective_chat.id
    try:
        index = int(context.args[0])
        if 0 < index <= len(match_id_list):
            match_url = match_id_list[index-1]
            await context.bot.send_message(chat_id=chat_id, text=match_list[index])

            task = context.user_data.get('message_task')
            if task and not task.done():
                task.cancel()

            task = asyncio.create_task(match_updates(match_url,chat_id,context))
            context.user_data['message_task'] = task

        else:
            await context.bot.send_message(chat_id=chat_id, text='Invalid index. Please provide a valid index.')

    except (IndexError, ValueError):
        await context.bot.send_message(chat_id=chat_id, text='Usage: /match <match no.>')

async def start(update=Update, context=ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(chat_id=update.effective_chat.id, text='Hi, welcome to Cricket alert bot. To see matches type /matches')

async def matches(Update=Update, context=ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(chat_id=Update.effective_chat.id, text = match_list_str)

start_handler = CommandHandler('start', start)
match_handler = CommandHandler('matches', matches)
event_handler = CommandHandler('match', get_event)
stop_handler = CommandHandler('stop', stop)

application.add_handler(start_handler)
application.add_handler(match_handler)
application.add_handler(event_handler)
application.add_handler(stop_handler)
''''
PORT = int(os.environ.get('PORT', '443'))
HOOK_URL = 'YOUR-CODECAPSULES-URL-HERE' + '/' + TOKEN
application.run_webhook(listen='0.0.0.0', port=PORT, url_path=TOKEN, webhook_url=HOOK_URL)
'''
application.run_polling()
async def main():
     while True:
         await asyncio.sleep(1)

if __name__=='__main__':
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())