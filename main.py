import telebot, time, requests, json, random, schedule
from threading import Thread

class Quote:
    def __init__(self, text="", title="", author=""):
        self.text = text
        self.title = title
        self.author = author

def getUsers():
    with open("users.json", "r") as f:
        usersDb = json.load(f)
    return usersDb

TIME = "08:00"

with open("utilities/token.txt", "r") as f:
    API_KEY = f.read()

bot = telebot.TeleBot(API_KEY)

def createHeaders(token: str):
    return {
        "Authorization": "Bearer " +  token,
        "Content-Type": "application/json",
        "Notion-Version": "2022-06-28"
    }

def readDatabase(token : str, databaseId : str):
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
            author = el["properties"]["Author"]["rollup"]["array"][0]["rich_text"][0]["text"]["content"]
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

def getRandomQuote(user):
    quotes = readDatabase(user["token"], user["databaseId"])
    if quotes != None and len(quotes) != 0:
        randomQuote: Quote = quotes[random.randint(0, len(quotes)-1)]
        return randomQuote
    else:
        return None

def sendQuote(quote: Quote, userKey: str):
    bot.send_message(userKey, quote.text)
    titleAuthor = f'"{quote.title}" - {quote.author}'
    bot.send_message(userKey, titleAuthor)

def autoQuote():
    users = getUsers()
    for userKey in users:
        randomQuote = getRandomQuote(users[userKey])
        if randomQuote != None:
            sendQuote(randomQuote, userKey)
   
def checkToken(message : telebot.types.Message):
    users = getUsers()
    userKey = str(message.chat.id)
    if userKey in users.keys() and users[userKey]["init"] == False and "token" not in users[userKey].keys():
        if message.text != None and message.text.split('_')[0] == "secret":
            users[userKey]["token"] = message.text
            with open("users.json", "w") as f:
                json.dump(users, f)
            return True
        bot.send_message(userKey, "Notion token not valid, try to send it again")
        return False
    elif userKey not in users.keys():
        bot.send_message(userKey, "Use the command /start to initialize the bot")
    return False

def checkDatabaseId(message : telebot.types.Message):
    users = getUsers()
    userKey = str(message.chat.id)
    if userKey in users.keys() and users[userKey]["init"] == False and "databaseId" not in users[userKey].keys():
        if message.text != None and len(message.text) >= 25:
            users[userKey]["databaseId"] = message.text
            with open("users.json", "w") as f:
                json.dump(users, f)
            return True
        bot.send_message(userKey, "Database Id not valid, try to send it again")
    return False

@bot.message_handler(commands=["start"])
def start(message : telebot.types.Message):
    users = getUsers()
    userKey = str(message.chat.id)
    bot.send_message(userKey, "Welcome to the Quotes Bot")
    if userKey not in users.keys():
        users[userKey] = {}
        users[userKey]["init"] = False
        with open("users.json", "w") as f:
            json.dump(users, f)
    if users[userKey]["init"] == False:
        bot.send_message(userKey, "Send the Notion token")

@bot.message_handler(commands=["quote"])
def quote(message : telebot.types.Message):
    users = getUsers()
    userKey = str(message.chat.id)
    if userKey in users.keys() and users[userKey]["init"] == True:
        randomQuote = getRandomQuote(users[userKey])
        if randomQuote != None:
            sendQuote(randomQuote, userKey)

@bot.message_handler(commands=["help"])
def help(message : telebot.types.Message):
    with open("commands.txt", "r") as f:
        commands = f.read()
    bot.send_message(str(message.chat.id), commands)

@bot.message_handler(func=checkToken)
def verifyToken(message : telebot.types.Message):
    bot.send_message(str(message.chat.id), "Send the Notion database Id")

@bot.message_handler(func=checkDatabaseId)
def verifyDatabase(message : telebot.types.Message):
    users = getUsers()
    userKey = str(message.chat.id)
    if message.text != None and readDatabase(users[userKey]["token"], message.text) == None:
        del users[userKey]["token"]
        del users[userKey]["databaseId"]
        bot.send_message(userKey, "Token or Database Id not valid, send the token again")
    else:
        users[userKey]["databaseId"] = message.text
        users[userKey]["init"] = True
        bot.send_message(userKey, "Setup completed!")
        with open("users.json", "w") as f:
            json.dump(users, f)

if __name__ == "__main__":
    schedule.every().day.at(TIME).do(autoQuote)
    Thread(target=scheduleChecker).start()
    bot.polling()
