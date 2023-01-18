import telebot, os, time, requests, json, random, schedule
from threading import Thread
from keep_alive import keep_alive
from replit import db

API_KEY = os.environ['API_KEY']

init = {}
newPage = {}

#at this time it will be sent an automatic quote from the user's personal notion page
TIME = "12:30"

#bot initialization                    
quotesbot = telebot.TeleBot(API_KEY)

#creates the headers to access the notion API
def createHeaders(token):
    headers = {
        "Authorization": "Bearer " + token,
        "Content-Type": "application/json",
        "Notion-Version": "2022-06-28"
    }
    return headers

#reads the user's notion page's database
def readDatabase(token, databaseId, quotes):
    headers = createHeaders(token)
    readUrl = f"https://api.notion.com/v1/databases/{databaseId}/query"
    res = requests.request("POST", readUrl, headers=headers)
    data = res.json()
    for el in data["results"]:
        text = el["properties"]["Text"]["rich_text"][0]["text"]["content"]
        title = el["properties"]["Name"]["title"][0]["plain_text"]
        try:
            author = el["properties"]["Author"]["rollup"]["array"][0]["rich_text"][0]["text"]["content"]    
        except:
            author = el["properties"]["Author"]["rich_text"][0]["text"]["content"]
        quotes.append([text, title, author])

#looks every second for schedules to run
def schedule_checker():
    while True:
        schedule.run_pending()
        time.sleep(1)

#daily automatic quote from the user's personal notion page
def automaticQuote():  #list(db.keys()) keys, token, databaseId
    for item in db.items():
        chatId = item[0]
        token = item[1][0]
        databaseId = item[1][1]
        quotes = []
        readDatabase(token, databaseId, quotes)
        randomQuote = random.randint(0, len(quotes)-1)
        quotesbot.send_message(chatId, quotes[randomQuote][0])
        time.sleep(2)
        titleAuthor = f'"{quotes[randomQuote][1]}" - {quotes[randomQuote][2]}'
        quotesbot.send_message(chatId, titleAuthor)

#checks if the user sent a valid Notion token
def checkToken(message):
    if str(message.chat.id) in db and ("initialized" not in db[str(message.chat.id)] or db[str(message.chat.id)][2] != "initialized"):
        global init
        if init[message.chat.id][1] == 0 and init[message.chat.id][0] == 0:
            if message.text.split('_')[0] == "secret":
                db[str(message.chat.id)].append(message.text)
                init[message.chat.id][0] = 1
                return True
            quotesbot.send_message(message.chat.id, "Notion token not valid, try to send it again")
            return False
    elif str(message.chat.id) not in db:
        quotesbot.send_message(message.chat.id, "Use the command /start to initialize the bot")
    return False

#checks if the user sent a valid Notion database ID
def checkDatabseId(message):
    if str(message.chat.id) in db and ("initialized" not in db[str(message.chat.id)] or db[str(message.chat.id)][2] != "initialized"):
        global init
        if init[message.chat.id][0] == 1 and init[message.chat.id][1] == 0:
            if len(message.text) >= 25:
                db[str(message.chat.id)].append(message.text)
                init[message.chat.id][1] = 1
                return True
            quotesbot.send_message(message.chat.id, "Database ID not valid, try to send it again")
    return False

#checks if the user has sent the title for a new quote    
def checkTitle(message):
    if message.chat.id in newPage and len(newPage[message.chat.id])==0:
        if message.text[:7] == "Title: ":
            newPage[message.chat.id].append(message.text[7:])
            return True
        else:
            quotesbot.send_message(message.chat.id, 'Error, type "Title: " followed by the title of the new page')
    return False

#checks if the user has sent the new quote's author's name
def checkAuthor(message):
    if message.chat.id in newPage and len(newPage[message.chat.id])==1:
        if message.text[:8] == "Author: ":
            newPage[message.chat.id].append(message.text[8:])  
            return True
        else:
            quotesbot.send_message(message.chat.id, 'Error, type "Author: " followed by the author\'s name')
    return False

#checks if the user has sent the content for a new quote
def checkContent(message):
    if message.chat.id in newPage and len(newPage[message.chat.id])==2:
        if message.text[:9] == "Content: ":
            newPage[message.chat.id].append(message.text[9:]) 
            return True
        else:
            quotesbot.send_message(message.chat.id, 'Error, type "Content: " followed by the quote you want to add')
    return False

#checks if the user has sent an emoji for a new quote
def checkEmoji(message):
    if message.chat.id in newPage and len(newPage[message.chat.id])==3:
        if "no" in message.text.lower():
            newPage[message.chat.id].append(0)
            return True
        elif message.text[:7] == "Emoji: ":
            emojiCode = (message.text[7]) 
            newPage[message.chat.id].append(emojiCode)
            return True
        else:
            quotesbot.send_message(message.chat.id, 'Error, type: "Emoji: " followed by the emoji that suits the most the quote you are adding (type "no" if you don\'t want to add an emoji)')
    return False

#the command /start greets the user, uses the chat ID to create a new key in the replit database and asks the user to send the notion token
@quotesbot.message_handler(commands=["start"])
def start(message):
    quotesbot.send_chat_action(message.chat.id, "typing")
    time.sleep(1)
    quotesbot.send_message(message.chat.id, "Welcome to the Quotes Bot!")
    quotesbot.send_chat_action(message.chat.id, "typing")
    time.sleep(1)
    quotesbot.send_message(message.chat.id, "Let's get you ready to start using the bot")
    if str(message.chat.id) not in db:
        db[str(message.chat.id)] = []
    if len(db[str(message.chat.id)])==0 or db[str(message.chat.id)][2] != "initialized":
        tokenOk = 0
        databaseIdOk = 0
        init[message.chat.id] = []
        init[message.chat.id].append(tokenOk)
        init[message.chat.id].append(databaseIdOk)
        quotesbot.send_message(message.chat.id, "Send the Notion token")

#the command /quote accesses the user's notion database and sends a random quote from it
@quotesbot.message_handler(commands=["quote"])
def sendQuote(message):
    if str(message.chat.id) in db and len(db[str(message.chat.id)])!=0 and db[str(message.chat.id)][2] == "initialized":
        quotes = []
        readDatabase(db[str(message.chat.id)][0], db[str(message.chat.id)][1], quotes)
        randomQuote = random.randint(0, len(quotes)-1)
        quotesbot.send_message(message.chat.id, quotes[randomQuote][0])
        time.sleep(2)
        titleAuthor = f'"{quotes[randomQuote][1]}" - {quotes[randomQuote][2]}'
        quotesbot.send_message(message.chat.id, titleAuthor)

#the command /new asks the user to send a title for the new notion page and the content (the emoji is optional), then creates the new notion quote page
@quotesbot.message_handler(commands=["new"])
def createQuote(message):
    if str(message.chat.id) in db and len(db[str(message.chat.id)])!=0 and db[str(message.chat.id)][2] == "initialized":
        databaseId = db[str(message.chat.id)][1]
        headers = createHeaders(db[str(message.chat.id)][0])
        newPage[message.chat.id] = []
        quotesbot.send_message(message.chat.id, 'Type "Title: " followed by the title of the new page')
        while len(newPage[message.chat.id]) != 4:
            time.sleep(1)
        createUrl = "https://api.notion.com/v1/pages"
        pageName = newPage[message.chat.id][0]
        pageAuthor = newPage[message.chat.id][1]
        pageContent = newPage[message.chat.id][2]

        if newPage[message.chat.id][3] != 0:
            emojiImg = newPage[message.chat.id][3]     
            newPageData = {
                "icon": {
                    "type": "emoji",                                      
                        "emoji": emojiImg
                    },
                "parent": {"database_id": databaseId},
                "properties": { 
                    "Author": {
                        "rich_text": [
                            {
                                "text": {
                                    "content": pageAuthor
                                }
                            }
                        ]
                    },
                    "Name": {
                        "title": [
                            {
                                "text": {
                                    "content": pageName
                                }
                            }
                        ]
                    },      
                    "Text": {
                        "rich_text": [
                            {
                                "text": {
                                    "content": pageContent
                                }
                            }
                        ]
                    }
                }
            }

        else:
            newPageData = {
                "parent": {"database_id": databaseId},
                "properties": { 
                    "Author": {
                        "rich_text": [
                            {
                                "text": {
                                     "content": pageAuthor
                                }
                            }
                        ]
                    },
                    "Name": {
                        "title": [
                            {
                                "text": {
                                    "content": pageName
                                }
                            }
                        ]
                    },
                    "Text": {
                        "rich_text": [
                            {
                                "text": {
                                    "content": pageContent
                                }
                            }
                        ]
                    }
                }
            }       
        data = json.dumps(newPageData)
        res = requests.request("POST", createUrl, headers=headers, data=data)
        if res.status_code == 200:
            quotesbot.send_message(message.chat.id ,"Page created!")
        else:
            if newPage[message.chat.id][3] != 0:
                emojiImg = newPage[message.chat.id][3]     
                newPageData = {
                    "icon": {
                            "type": "emoji",                                      
                            "emoji": emojiImg
                        },
                    "parent": {"database_id": databaseId},
                    "properties": { 
                        "Name": {
                            "title": [
                                {
                                    "text": {
                                        "content": pageName
                                    }
                                }
                            ]
                        },
                        "Text": {
                            "rich_text": [
                                {
                                    "text": {
                                        "content": pageContent
                                    }
                                }
                            ]
                        }
                    }
                }

            else:
                newPageData = {
                    "parent": {"database_id": databaseId},
                    "properties": { 
                        "Name": {
                            "title": [
                                {
                                    "text": {
                                        "content": pageName
                                    }
                                }
                            ]
                        },
                        "Text": {
                            "rich_text": [
                                {
                                    "text": {
                                        "content": pageContent
                                    }
                                }
                            ]
                        }
                    }
                }
            data = json.dumps(newPageData)
            res = requests.request("POST", createUrl, headers=headers, data=data)
            if res.status_code == 200:
                quotesbot.send_message(message.chat.id ,"Page created!")
            else:
                quotesbot.send_message(message.chat.id, "Sorry, there seems to be an error, try again with the command /new")

#stops the creation of a new page
@quotesbot.message_handler(commands=["cancel"])
def cancelNewPage(message):
    del newPage[message.chat.id]

#if the function checkToken returns True asks for the notion Database ID
@quotesbot.message_handler(func=checkToken)
def verifyToken(message):
    quotesbot.send_message(message.chat.id, "Send the Notion database ID")

#if the function checkDatabaseId returns True checks if the token and database ID are valid and if so sets the user as initialized,
#otherwise it asks the user to send the token and the database ID again
@quotesbot.message_handler(func=checkDatabseId)
def verifyDatabaseId(message):
    global init
    headers = createHeaders(db[str(message.chat.id)][0])
    readUrl = f"https://api.notion.com/v1/databases/{db[str(message.chat.id)][1]}/query"
    res = requests.request("POST", readUrl, headers=headers)
    if res.status_code != 200:
        del db[str(message.chat.id)][0]
        del db[str(message.chat.id)][0]
        quotesbot.send_message(message.chat.id, "Token or database ID not valid, resend the token")
        init[message.chat.id][0] = 0
        init[message.chat.id][1] = 0
    else:
        quotesbot.send_message(message.chat.id, "Setup completed!")
        db[str(message.chat.id)].append("initialized")
        del init[message.chat.id]

#if the function checkTitle returns True asks the user to send the content for the new quote
@quotesbot.message_handler(func=checkTitle)
def verifyTitle(message):
    quotesbot.send_message(message.chat.id, 'Type: "Author: " followed by the author\'s name')

#calls the checkAuthor function
@quotesbot.message_handler(func=checkAuthor)
def verifyAuthor(message):
    quotesbot.send_message(message.chat.id, 'Type: "Content: " followed by the quote you want to add')

#if the function checkContent returns True asks the user to sent an emoji for the new quote
@quotesbot.message_handler(func=checkContent)
def verifyContent(message):
    quotesbot.send_message(message.chat.id, 'Type "Emoji: " followed by the emoji that suits the most the quote you are adding (type "No" if you don\'t want to add an emoji)')

#calls the checkEmoji function
@quotesbot.message_handler(func=checkEmoji)
def verifyEmoji(message):
    pass

if __name__ == "__main__":
    #schedules the daily quote
    schedule.every().day.at(TIME).do(automaticQuote)
    Thread(target=schedule_checker).start() 
    keep_alive()
    quotesbot.polling()