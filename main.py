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

bot = telebot.TeleBot("5582618835:AAEmHG-rXVo6d2W7-gy-RATNjy99-JvuFHo")

def createHeaders(token: str):
    return {
        "Authorization": "Bearer " +  token,
        "Content-Type": "application/json",
        "Notion-Version": "2022-06-28"
    }

def readDatabase(token, databaseId):
    headers = createHeaders(token)
    readUrl = f"https://api.notion.com/v1/databases/{databaseId}/query"
    res = requests.request("POST", readUrl, headers=headers)
    if res.status_code != 200:
        return None
    data = res.json()
    quotes = []
    for el in data["results"]:
        textObj = el["properties"]["Text"]["rich_text"]
        text = ''
        for phrase in textObj:
            text += phrase["text"]["content"]
        title = el["properties"]["Name"]["title"][0]["plain_text"]
        try:
            author = el["properties"]["Author"]["rollup"]["array"][0]["rich_text"][0]["text"]["content"]
        except:
            author = el["properties"]["Author"]["rich_text"][0]["text"]["content"]
        quotes.append(Quote(text, title, author))
    return quotes

def scheduleChecker():
    while True:
        schedule.run_pending()
        time.sleep(1)

def getRandomQuote(user):
    quotes = readDatabase(user["token"], user["databaseId"])
    if quotes != None:
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
   
def checkToken(message):
    users = getUsers()
    userKey = str(message.chat.id)
    if userKey in users.keys() and users[userKey]["init"] == False and "token" not in users[userKey].keys():
        if message.text.split('_')[0] == "secret":
            users[userKey]["token"] = message.text
            with open("users.json", "w") as f:
                json.dump(users, f)
            return True
        bot.send_message(userKey, "Notion token not valid, try to send it again")
        return False
    elif userKey not in users.keys():
        bot.send_message(userKey, "Use the command /start to initialize the bot")
    return False

def checkDatabaseId(message):
    users = getUsers()
    userKey = str(message.chat.id)
    if userKey in users.keys() and users[userKey]["init"] == False and "databaseId" not in users[userKey].keys():
        if len(message.text) >= 25:
            users[userKey]["databaseId"] = message.text
            with open("users.json", "w") as f:
                json.dump(users, f)
            return True
        bot.send_message(userKey, "Database Id not valid, try to send it again")
    return False

@bot.message_handler(commands=["start"])
def start(message):
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
def quote(message):
    users = getUsers()
    userKey = str(message.chat.id)
    if userKey in users.keys() and users[userKey]["init"] == True:
        randomQuote = getRandomQuote(users[userKey])
        if randomQuote != None:
            sendQuote(randomQuote, userKey)

@bot.message_handler(func=checkToken)
def verifyToken(message):
    bot.send_message(str(message.chat.id), "Send the Notion database Id")

@bot.message_handler(func=checkDatabaseId)
def verifyDatabase(message):
    users = getUsers()
    userKey = str(message.chat.id)
    if readDatabase(users[userKey]["token"], message.text) == None:
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
