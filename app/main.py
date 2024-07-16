"""
Main module
starts the bot
"""

from threading import Thread
from time import sleep

from bot import bot, send_quote
from schedule import every, run_pending
from utils import get_random_quote, get_users

TIME = "08:00"


def schedule_checker():
    """
    check every second if a scheduled function needs to be executed
    """

    while True:
        run_pending()
        sleep(1)


def auto_quote():
    """
    function used by the scheduler to send a random quote
    for every user
    """

    users = get_users()
    for user_key in users:
        random_quote = get_random_quote(users[user_key])
        send_quote(random_quote, user_key)


def main():
    """
    start the bot
    """

    every().day.at(TIME).do(auto_quote)
    Thread(target=schedule_checker).start()
    bot.infinity_polling()


if __name__ == "__main__":
    main()
