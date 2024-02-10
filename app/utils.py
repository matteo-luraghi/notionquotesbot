from requests import post as reqpost
from json import load as jload
from random import randint

class Quote:
    def __init__(self, text="", title="", author=""):
        self.text = text
        self.title = title
        self.author = author

    def __str__(self):
        return f"{self.text}\n\n{self.title} - {self.author}"

#returns all the users
def getUsers() -> dict:
    with open("data/users.json", "r") as f:
        usersDb = jload(f)
    return usersDb

def getQuotes(userKey: str) -> list[Quote] | None:
    users = getUsers()
    quotes = readDatabase(users[userKey]["token"], users[userKey]["databaseId"])
    return quotes

#returns the list of quotes from the user's database
def readDatabase(token : str, databaseId : str) -> list[Quote] | None:
    headers = {
        "Authorization": "Bearer " +  token,
        "Content-Type": "application/json",
        "Notion-Version": "2022-06-28"
    }
    readUrl = f"https://api.notion.com/v1/databases/{databaseId}/query"
    res = reqpost(readUrl, headers=headers)
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

#returns a random quote from the user's database
def getRandomQuote(user : dict) -> Quote | None:
    quotes = readDatabase(user["token"], user["databaseId"])
    if quotes != None:
        if len(quotes) != 0:
            randomQuote: Quote = quotes[randint(0, len(quotes)-1)]
            return randomQuote
    return None

def getAuthors(userKey: str) -> set | None:
    users = getUsers()
    authors = {""}
    authors.remove("")
    if userKey in users.keys() and users[userKey]["init"] == True:
        quotes = readDatabase(users[userKey]["token"], users[userKey]["databaseId"])
        if quotes != None:
            authors = {quote.author for quote in quotes}
    return authors

def getTitles(userKey: str) -> set | None:
    users = getUsers()
    titles = {""}
    titles.remove("")
    if userKey in users.keys() and users[userKey]["init"] == True:
        quotes = readDatabase(users[userKey]["token"], users[userKey]["databaseId"])
        if quotes != None:
            titles = {quote.title for quote in quotes}
    return titles

def getTitlesAuthor(userKey: str, author: str) -> set | None:
    author = author.lower()
    users = getUsers()
    titles = {""}
    titles.remove("")
    if userKey in users.keys() and users[userKey]["init"] == True:
        quotes = readDatabase(users[userKey]["token"], users[userKey]["databaseId"])
        if quotes != None:
            titles = {quote.title for quote in quotes if author in quote.author.lower() or author == quote.author.lower()}
    return titles
