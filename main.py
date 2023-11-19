import telebot, time, requests, json, random, schedule, os
from threading import Thread
from dotenv import load_dotenv

class Quote:
    def __init__(self, text="", title="", author=""):
        self.text = text
        self.title = title
        self.author = author

def getUsers() -> dict:
    with open("users.json", "r") as f:
        usersDb = json.load(f)
    return usersDb

TIME = "08:00"

try:
    load_dotenv('.env')
except:
    print("Failed to load .env")

API_KEY = None
while API_KEY == None:
    API_KEY = os.getenv("API_KEY")
bot = telebot.TeleBot(API_KEY)
bot.enable_save_next_step_handlers(delay=1)
bot.load_next_step_handlers()

def createHeaders(token: str) -> dict:
    return {
        "Authorization": "Bearer " +  token,
        "Content-Type": "application/json",
        "Notion-Version": "2022-06-28"
    }

def readDatabase(token : str, databaseId : str) -> list[Quote] | None:
    headers = createHeaders(token)
    readUrl = f"https://api.notion.com/v1/databases/{databaseId}/query"
    res = requests.request("POST", readUrl, headers=headers)
    if res.status_code != 200:
        return None
    data = res.json()
    quotes = []
    for el in data["results"]:
        try: 
            textObj = el["properties"]["Text"]["rich_text"]
            text = ''
            for phrase in textObj:
                text += phrase["text"]["content"]
        except:
            text = ''
        try:
            title = el["properties"]["Name"]["title"][0]["plain_text"]
        except:
            title = ''
        try:
            author = el["properties"]["AuthorB"]["rollup"]["array"][0]["rich_text"][0]["text"]["content"]
        except:
            try:
                author = el["properties"]["Author"]["rich_text"][0]["text"]["content"]
            except:
                author = ''
        if text != '' and title != '' and author != '':
            quotes.append(Quote(text, title, author))
    return quotes

def scheduleChecker():
    while True:
        schedule.run_pending()
        time.sleep(1)

def getRandomQuote(user : dict, userKey : str) -> Quote | None:
    quotes = readDatabase(user["token"], user["databaseId"])
    if quotes != None:
        if len(quotes) != 0:
            randomQuote: Quote = quotes[random.randint(0, len(quotes)-1)]
            return randomQuote
        else:
            bot.send_message(userKey, "There are no quotes in your database!")
    return None

def sendQuote(quote: Quote, userKey: str):
    bot.send_message(userKey, quote.text)
    titleAuthor = f'"{quote.title}" - {quote.author}'
    bot.send_message(userKey, titleAuthor)

def autoQuote():
    users = getUsers()
    for userKey in users:
        randomQuote = getRandomQuote(users[userKey], userKey)
        if randomQuote != None:
            sendQuote(randomQuote, userKey)
   
def checkToken(message : telebot.types.Message):
    users = getUsers()
    userKey = str(message.chat.id)
    if userKey in users.keys() and users[userKey]["init"] == False:
        if "token" not in users[userKey].keys():
            if message.text != None and message.text.split('_')[0] == "secret":
                users[userKey]["token"] = message.text
                with open("users.json", "w") as f:
                    json.dump(users, f)
                bot.send_message(userKey, "Send the Notion database ID")
                bot.register_next_step_handler(message, checkDatabaseId)
            else:
                bot.send_message(userKey, "Notion token not valid, use the /start command to try again")
        else:
            bot.send_message(userKey, "Send the Notion database ID")
            bot.register_next_step_handler(message, checkDatabaseId)
    elif userKey not in users.keys():
        bot.send_message(userKey, "Use the /start command to initialize the bot")

def checkDatabaseId(message : telebot.types.Message):
    users = getUsers()
    userKey = str(message.chat.id)
    if userKey in users.keys() and users[userKey]["init"] == False and "databaseId" not in users[userKey].keys():
        if message.text != None and len(message.text) >= 25:
            users[userKey]["databaseId"] = message.text
            with open("users.json", "w") as f:
                json.dump(users, f)
            if readDatabase(users[userKey]["token"], users[userKey]["databaseId"]) == None:
                del users[userKey]["token"]
                del users[userKey]["databaseId"]
                with open("users.json", "w") as f:
                    json.dump(users, f)
                bot.send_message(userKey, "Token or Database Id not valid, use the /start command to try again")
            else:
                users[userKey]["init"] = True
                bot.send_message(userKey, "Setup completed!")
                with open("users.json", "w") as f:
                    json.dump(users, f)
        else:
            bot.send_message(userKey, "Database Id not valid, use the /start command to try again")

@bot.message_handler(commands=["start"])
def start(message : telebot.types.Message):
    users = getUsers()
    userKey = str(message.chat.id)
    if userKey not in users.keys():
        bot.send_message(userKey, "Welcome to the Quotes Bot")
        users[userKey] = {}
        users[userKey]["init"] = False
        with open("users.json", "w") as f:
            json.dump(users, f)
    if users[userKey]["init"] == False:
        bot.send_message(userKey, "Send the Notion token")
        bot.register_next_step_handler(message, checkToken)
    else:
        bot.send_message(userKey, "You are ready to use the bot!")

@bot.message_handler(commands=["quote"])
def quote(message : telebot.types.Message):
    users = getUsers()
    userKey = str(message.chat.id)
    if userKey in users.keys() and users[userKey]["init"] == True:
        randomQuote = getRandomQuote(users[userKey], userKey)
        if randomQuote != None:
            sendQuote(randomQuote, userKey)
    else:
        bot.send_message(userKey, "Use the /start command to setup the bot")

@bot.message_handler(commands=["help"])
def help(message : telebot.types.Message):
    with open("commands.txt", "r") as f:
        commands = f.read()
    bot.send_message(str(message.chat.id), commands)
    
if __name__ == "__main__":
    schedule.every().day.at(TIME).do(autoQuote)
    Thread(target=scheduleChecker).start()
    bot.infinity_polling()
