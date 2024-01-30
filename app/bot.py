from json import dump as jdump
from os import getenv
from telebot.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from telebot import TeleBot
import utils

API_KEY = getenv("API_KEY")
try:
    import config
    API_KEY = config.test_api_key
except:
    pass

#initialization
bot = TeleBot(API_KEY)
bot.enable_save_next_step_handlers(delay=1)
bot.load_next_step_handlers()

def sendQuote(quote: utils.Quote | None, userKey: str):
    if quote != None:
        bot.send_message(userKey, str(quote))

def sendQuoteAuthor(userKey: str, author: str):
    author = author.lower()
    quotes = utils.getQuotes(userKey)
    if quotes != None:
        for quote in quotes:
            if author in quote.author.lower().split(" ") or author == quote.author.lower():
                sendQuote(quote, userKey)

def sendQuoteTitle(userKey: str, title: str):
    title = title.lower()
    quotes = utils.getQuotes(userKey)
    if quotes != None:
        for quote in quotes:
            if title in quote.title.lower() or title == quote.title.lower():
                sendQuote(quote, userKey)

#checks if the token is valid and if so saves it temporarely
def checkToken(message : Message):
    users = utils.getUsers()
    userKey = str(message.chat.id)
    if userKey in users.keys() and users[userKey]["init"] == False:
        if "token" not in users[userKey].keys():
            if message.text != None and message.text.split('_')[0] == "secret":
                users[userKey]["token"] = message.text
                with open("data/users.json", "w") as f:
                    jdump(users, f)
                bot.send_message(userKey, "Send the Notion database ID")
                bot.register_next_step_handler(message, checkDatabaseId)
            else:
                bot.send_message(userKey, "Notion token not valid, use the /start command to try again")
        else:
            bot.send_message(userKey, "Send the Notion database ID")
            bot.register_next_step_handler(message, checkDatabaseId)
    elif userKey not in users.keys():
        bot.send_message(userKey, "Use the /start command to initialize the bot")

#checks if the database ID is valid and if, combined with the token
#the bot manages to connect to notion, it saves the user
def checkDatabaseId(message : Message):
    users = utils.getUsers()
    userKey = str(message.chat.id)
    if userKey in users.keys() and users[userKey]["init"] == False and "databaseId" not in users[userKey].keys():
        if message.text != None and len(message.text) >= 25:
            users[userKey]["databaseId"] = message.text
            with open("data/users.json", "w") as f:
                jdump(users, f)
            if utils.readDatabase(users[userKey]["token"], users[userKey]["databaseId"]) == None:
                del users[userKey]["token"]
                del users[userKey]["databaseId"]
                with open("data/users.json", "w") as f:
                    jdump(users, f)
                bot.send_message(userKey, "Token or Database Id not valid, use the /start command to try again")
            else:
                users[userKey]["init"] = True
                bot.send_message(userKey, "Setup completed!")
                with open("data/users.json", "w") as f:
                    jdump(users, f)
        else:
            bot.send_message(userKey, "Database Id not valid, use the /start command to try again")

#bot's commands
@bot.message_handler(commands=["start"])
def start(message : Message):
    users = utils.getUsers()
    userKey = str(message.chat.id)
    if userKey not in users.keys():
        bot.send_message(userKey, "Welcome to the Quotes Bot")
        users[userKey] = {}
        users[userKey]["init"] = False
        with open("data/users.json", "w") as f:
            jdump(users, f)
    if users[userKey]["init"] == False:
        bot.send_message(userKey, "Send the Notion token")
        bot.register_next_step_handler(message, checkToken)
    else:
        bot.send_message(userKey, "You are ready to use the bot!")

@bot.message_handler(commands=["quote"])
def quote(message : Message):
    users = utils.getUsers()
    userKey = str(message.chat.id)
    if userKey in users.keys() and users[userKey]["init"] == True:
        randomQuote = utils.getRandomQuote(users[userKey])
        if randomQuote != None:
            sendQuote(randomQuote, userKey)
    else:
        bot.send_message(userKey, "Use the /start command to setup the bot")

@bot.message_handler(commands=["author", "title"])
def searchAuthor(message: Message):
    try:
        command, search = str(message.text).split(" ", 1)
    except:
        bot.send_message(message.chat.id, f"Write the name after the command\nEx. {message.text} name")
        return
    userKey = str(message.chat.id)
    match command:
        case "/author": sendQuoteAuthor(userKey, search)
        case "/title": sendQuoteTitle(userKey, search)
    
@bot.message_handler(commands=["authors"])
def authorsList(message: Message):
    userKey = str(message.chat.id)
    authors = utils.getAuthors(userKey)
    if authors != None:
        markup = InlineKeyboardMarkup()
        for author in authors:
            markup.add(InlineKeyboardButton(author, callback_data=f"author_{author}"))
        bot.send_message(message.chat.id, "Choose:", reply_markup=markup)

@bot.message_handler(commands=["titles"])
def titlesList(message: Message):
    userKey = str(message.chat.id)
    titles = utils.getTitles(userKey)
    if titles != None:
        markup = InlineKeyboardMarkup()
        for title in titles:
            markup.add(InlineKeyboardButton(title, callback_data=f"title_{title}"))
        bot.send_message(message.chat.id, "Choose:", reply_markup=markup)

@bot.message_handler(commands=["titleauthor"])
def titleAuthor(message: Message):
    userKey = str(message.chat.id)
    try:
        author = str(message.text).split(" ", 1)[1]
    except:
        bot.send_message(message.chat.id, "Write the name of the author after the command\nEx. /titleauthor pirandello")
        return
    titlesAuthor = utils.getTitlesAuthor(userKey, author)
    if titlesAuthor != None:
        markup = InlineKeyboardMarkup()
        for title in titlesAuthor:
            markup.add(InlineKeyboardButton(title, callback_data=f"title_{title}"))
        bot.send_message(message.chat.id, "Choose:", reply_markup=markup)

@bot.message_handler(commands=["help"])
def help(message : Message):
    with open("utilities/commands.txt", "r") as f:
        commands = f.read()
    bot.send_message(str(message.chat.id), commands)

@bot.callback_query_handler(func=lambda callback: callback.data.startswith("author_"))
def filterAuthor(callback):
    author = callback.data.split("_")[1]
    sendQuoteAuthor(str(callback.message.chat.id), author)

@bot.callback_query_handler(func=lambda callback: callback.data.startswith("title_"))
def filterTitle(callback):
    title = callback.data.split("_")[1]
    sendQuoteTitle(str(callback.message.chat.id), title)
