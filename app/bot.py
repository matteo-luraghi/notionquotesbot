"""
Bot module
handles the bot creation and commands
"""

from json import dump as jdump
from os import getenv

import utils
from telebot import TeleBot
from telebot.types import InlineKeyboardButton, InlineKeyboardMarkup, Message

# if API_KEY is an env variable, for production
API_KEY = getenv("API_KEY")

# if TEST_API_KEY is saved in config.py, for testing
try:
    import config

    API_KEY = config.TEST_API_KEY

except ModuleNotFoundError:
    pass

if API_KEY is None:
    raise RuntimeError("API key not configured")


# initialization
bot = TeleBot(API_KEY)
bot.enable_save_next_step_handlers(delay=1)
bot.load_next_step_handlers()


def send_quote(quote: utils.Quote | None, user_key: str):
    """
    send the quote to the user
    """

    if quote is not None:
        bot.send_message(user_key, str(quote))


def send_quote_author(user_key: str, author: str):
    """
    send all quotes from an author to the user
    """

    author = author.lower()
    quotes = utils.get_quotes(user_key)
    if quotes is not None:
        for quote in quotes:
            if (
                author in quote.author.lower().split(" ")
                or author == quote.author.lower()
            ):
                send_quote(quote, user_key)


def send_quote_title(user_key: str, title: str):
    """
    send all quotes from a book to the user
    """

    title = title.lower()
    quotes = utils.get_quotes(user_key)
    if quotes is not None:
        for quote in quotes:
            if title in quote.title.lower() or title == quote.title.lower():
                send_quote(quote, user_key)


def check_token(message: Message):
    """
    check if the token is valid and if so save it temporarely
    """

    users = utils.get_users()
    user_key = str(message.chat.id)
    if user_key in users.keys() and users[user_key]["init"] is False:
        if "token" not in users[user_key].keys():
            if message.text is not None and message.text.split("_")[0] == "secret":
                users[user_key]["token"] = message.text
                with open("data/users.json", mode="w", encoding="UTF-8") as f:
                    jdump(users, f)
                bot.send_message(user_key, "Send the Notion database ID")
                bot.register_next_step_handler(message, check_database_id)
            else:
                bot.send_message(
                    user_key,
                    "Notion token not valid, use the /start command to try again",
                )
        else:
            bot.send_message(user_key, "Send the Notion database ID")
            bot.register_next_step_handler(message, check_database_id)
    elif user_key not in users.keys():
        bot.send_message(user_key, "Use the /start command to initialize the bot")


def check_database_id(message: Message):
    """
    check if the database ID is valid and if, combined with the token
    the bot manages to connect to notion, save the user
    """

    users = utils.get_users()
    user_key = str(message.chat.id)
    if (
        user_key in users.keys()
        and users[user_key]["init"] is False
        and "databaseId" not in users[user_key].keys()
    ):
        if message.text is not None and len(message.text) >= 25:
            users[user_key]["databaseId"] = message.text
            with open("data/users.json", mode="w", encoding="UTF-8") as f:
                jdump(users, f)
            if (
                utils.read_database(
                    users[user_key]["token"], users[user_key]["databaseId"]
                )
                is None
            ):
                del users[user_key]["token"]
                del users[user_key]["databaseId"]
                with open("data/users.json", mode="w", encoding="UTF-8") as f:
                    jdump(users, f)
                bot.send_message(
                    user_key,
                    "Token or Database Id not valid, use the /start command to try again",
                )
            else:
                users[user_key]["init"] = True
                bot.send_message(user_key, "Setup completed!")
                with open("data/users.json", mode="w", encoding="UTF-8") as f:
                    jdump(users, f)
        else:
            bot.send_message(
                user_key, "Database Id not valid, use the /start command to try again"
            )


# bot's commands
@bot.message_handler(commands=["start"])
def start_command(message: Message):
    """
    start command
    initialize the bot
    """

    users = utils.get_users()
    user_key = str(message.chat.id)
    if user_key not in users.keys():
        bot.send_message(user_key, "Welcome to the Quotes Bot")
        users[user_key] = {}
        users[user_key]["init"] = False
        with open("data/users.json", mode="w", encoding="UTF-8") as f:
            jdump(users, f)
    if users[user_key]["init"] is False:
        bot.send_message(user_key, "Send the Notion token")
        bot.register_next_step_handler(message, check_token)
    else:
        bot.send_message(user_key, "You are ready to use the bot!")


@bot.message_handler(commands=["quote"])
def quote_command(message: Message):
    """
    quote command
    send a random quote
    """

    users = utils.get_users()
    user_key = str(message.chat.id)
    if user_key in users.keys() and users[user_key]["init"] is True:
        random_quote = utils.get_random_quote(users[user_key])
        if random_quote is not None:
            send_quote(random_quote, user_key)
    else:
        bot.send_message(user_key, "Use the /start command to setup the bot")


@bot.message_handler(commands=["author", "title"])
def search_command(message: Message):
    """
    author command
    title command
    send a quote from a specific author/title
    """

    try:
        command, search = str(message.text).split(" ", 1)
    except (ValueError, IndexError):
        bot.send_message(
            message.chat.id,
            f"Write the name after the command\nEx. {message.text} name",
        )
        return
    user_key = str(message.chat.id)
    match command:
        case "/author":
            send_quote_author(user_key, search)
        case "/title":
            send_quote_title(user_key, search)


@bot.message_handler(commands=["authors"])
def authors_list_command(message: Message):
    """
    authors command
    make the user choose an author
    """

    user_key = str(message.chat.id)
    authors = utils.get_authors(user_key)
    if authors is not None:
        markup = InlineKeyboardMarkup()
        for author in authors:
            markup.add(InlineKeyboardButton(author, callback_data=f"author_{author}"))
        bot.send_message(message.chat.id, "Choose:", reply_markup=markup)


@bot.message_handler(commands=["titles"])
def titles_list_command(message: Message):
    """
    titles command
    make the user choose a title
    """

    user_key = str(message.chat.id)
    titles = utils.get_titles(user_key)
    if titles is not None:
        markup = InlineKeyboardMarkup()
        for title in titles:
            markup.add(InlineKeyboardButton(title, callback_data=f"title_{title}"))
        bot.send_message(message.chat.id, "Choose:", reply_markup=markup)


@bot.message_handler(commands=["titleauthor"])
def title_author_command(message: Message):
    """
    titleauthor command
    filter for books written by the author
    ask the user to choose one title
    """

    user_key = str(message.chat.id)
    try:
        author = str(message.text).split(" ", 1)[1]
    except (ValueError, IndexError):
        bot.send_message(
            message.chat.id,
            "Write the name of the author after the command\nEx. /titleauthor pirandello",
        )
        return
    titles_author = utils.get_titles_author(user_key, author)
    if titles_author is not None:
        markup = InlineKeyboardMarkup()
        for title in titles_author:
            markup.add(InlineKeyboardButton(title, callback_data=f"title_{title}"))
        bot.send_message(message.chat.id, "Choose:", reply_markup=markup)


@bot.message_handler(commands=["help"])
def help_command(message: Message):
    """
    help command
    show all the available commands
    """

    with open("utilities/commands.txt", mode="r", encoding="UTF-8") as f:
        commands = f.read()
    bot.send_message(str(message.chat.id), commands)


@bot.callback_query_handler(func=lambda callback: callback.data.startswith("author_"))
def filter_author_command(callback):
    """
    callback from author command
    """

    author = callback.data.split("_")[1]
    send_quote_author(str(callback.message.chat.id), author)


@bot.callback_query_handler(func=lambda callback: callback.data.startswith("title_"))
def filter_title_command(callback):
    """
    callback from title command
    """

    title = callback.data.split("_")[1]
    send_quote_title(str(callback.message.chat.id), title)
