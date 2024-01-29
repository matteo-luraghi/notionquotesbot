from schedule import run_pending
from schedule import every
from time import sleep
from threading import Thread
from utils import getUsers, getRandomQuote
from bot import bot, sendQuote

TIME = "08:00"

def scheduleChecker():
    while True:
        run_pending()
        sleep(1)

#function used by the scheduler to send a random quote
#for every user
def autoQuote():
    users = getUsers()
    for userKey in users:
        randomQuote = getRandomQuote(users[userKey])
        sendQuote(randomQuote, userKey)
   
if __name__ == "__main__":
    every().day.at(TIME).do(autoQuote)
    Thread(target=scheduleChecker).start()
    bot.infinity_polling()
