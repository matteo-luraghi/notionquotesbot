import telebot
from json import dump as jdump
from os import getenv
import utils

API_KEY = getenv("API_KEY")
try:
    import config
    API_KEY = config.test_api_key
except:
    pass

#initialization
bot = telebot.TeleBot(API_KEY)
bot.enable_save_next_step_handlers(delay=1)
bot.load_next_step_handlers()

#sends a quote to the user if the database is not empty
def sendQuote(quote: utils.Quote | None, userKey: str):
    if quote != None:
        bot.send_message(userKey, quote.text)
        titleAuthor = f'"{quote.title}" - {quote.author}'
        bot.send_message(userKey, titleAuthor)
    else:
        bot.send_message(userKey, "There are no quotes in your database!")

#checks if the token is valid and if so saves it temporarely
def checkToken(message : telebot.types.Message):
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
def checkDatabaseId(message : telebot.types.Message):
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
def start(message : telebot.types.Message):
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
def quote(message : telebot.types.Message):
    users = utils.getUsers()
    userKey = str(message.chat.id)
    if userKey in users.keys() and users[userKey]["init"] == True:
        randomQuote = utils.getRandomQuote(users[userKey])
        if randomQuote != None:
            sendQuote(randomQuote, userKey)
    else:
        bot.send_message(userKey, "Use the /start command to setup the bot")

@bot.message_handler(commands=["help"])
def help(message : telebot.types.Message):
    with open("utilities/commands.txt", "r") as f:
        commands = f.read()
    bot.send_message(str(message.chat.id), commands)
