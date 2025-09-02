"""
Utils module
useful functions to manage the connection with the db
"""

import os
from json import dump as jdump
from json import load as jload
from random import randint

from requests import post as reqpost


class Quote:
    """
    Quote class
    saves text, title and author of the quote
    """

    def __init__(self, text="", title="", author=""):
        self._text = text
        self._title = title
        self._author = author

    def __str__(self):
        return f"{self.text}\n\n{self.title} - {self.author}"

    @property
    def text(self):
        """text getter"""
        return self._text

    @property
    def title(self):
        """title getter"""
        return self._title

    @property
    def author(self):
        """author getter"""
        return self._author


def get_users() -> dict:
    """
    get all the users
    """

    # initialize empty json file
    if not os.path.exists("data/users.json"):
        with open("data/users.json", mode="w", encoding="UTF-8") as f:
            jdump({}, f)

    with open("data/users.json", mode="r", encoding="UTF-8") as f:
        users_db = jload(f)
    return users_db


def get_quotes(user_key: str) -> list[Quote] | None:
    """
    exposed method
    get all the user's quotes
    """

    users = get_users()
    quotes = read_database(users[user_key]["token"], users[user_key]["databaseId"])
    return quotes


def read_database(token: str, database_id: str) -> list[Quote] | None:
    """
    get the list of quotes from the user's database
    """

    headers = {
        "Authorization": "Bearer " + token,
        "Content-Type": "application/json",
        "Notion-Version": "2022-06-28",
    }
    read_url = f"https://api.notion.com/v1/databases/{database_id}/query"

    quotes = []

    # true until all the quotes are available
    has_more = True
    next_cursor = None

    while has_more:
        payload = {"page_size": 100}
        if next_cursor:
            payload["start_cursor"] = next_cursor

        res = reqpost(read_url, headers=headers, json=payload, timeout=10)

        if res.status_code != 200:
            break

        data = res.json()

        # check if there are more results to fetch
        has_more = data.get("has_more", False)
        next_cursor = data.get("next_cursor", None)

        for el in data["results"]:
            try:
                text_obj = el["properties"]["Text"]["rich_text"]
                text = "".join(phrase["text"]["content"] for phrase in text_obj)
            except (KeyError, IndexError, TypeError):
                text = ""

            # general case
            try:
                title = el["properties"]["Book"]["rich_text"][0]["text"]["content"]
            except (KeyError, IndexError, TypeError):
                # personal case
                try:
                    title = el["properties"]["Name"]["title"][0]["plain_text"]
                except (KeyError, IndexError, TypeError):
                    title = ""
            # personal case
            try:
                author = el["properties"]["AuthorB"]["rollup"]["array"][0]["rich_text"][
                    0
                ]["text"]["content"]
            except (KeyError, IndexError, TypeError):
                # general case
                try:
                    author = el["properties"]["Author"]["rich_text"][0]["text"][
                        "content"
                    ]
                except (KeyError, IndexError, TypeError):
                    author = ""

            if text != "" and title != "" and author != "":
                quotes.append(Quote(text, title, author))

    return quotes


def get_random_quote(user: dict) -> Quote | None:
    """
    return a random quote from the user's database
    """

    quotes = read_database(user["token"], user["databaseId"])
    if quotes is not None:
        if len(quotes) != 0:
            random_quote: Quote = quotes[randint(0, len(quotes) - 1)]
            return random_quote
    return None


def get_authors(user_key: str) -> set | None:
    """
    return all the authors from the user's database
    """

    users = get_users()
    authors = {""}
    authors.remove("")
    if user_key in users.keys() and users[user_key]["init"] is True:
        quotes = read_database(users[user_key]["token"], users[user_key]["databaseId"])
        if quotes is not None:
            authors = {quote.author.strip() for quote in quotes}
    return authors


def get_titles(user_key: str) -> set | None:
    """
    return all the titles from the user's database
    """

    users = get_users()
    titles = {""}
    titles.remove("")
    if user_key in users.keys() and users[user_key]["init"] is True:
        quotes = read_database(users[user_key]["token"], users[user_key]["databaseId"])
        if quotes is not None:
            titles = {quote.title.strip() for quote in quotes}
    for title in titles:
        print(title)
    return titles


def get_titles_author(user_key: str, author: str) -> set | None:
    """
    return all the titles written by the author
    from the user's database
    """

    author = author.lower()
    users = get_users()
    titles = {""}
    titles.remove("")
    if user_key in users.keys() and users[user_key]["init"] is True:
        quotes = read_database(users[user_key]["token"], users[user_key]["databaseId"])
        if quotes is not None:
            titles = {
                quote.title.strip()
                for quote in quotes
                if author in quote.author.lower().strip()
                or author == quote.author.lower().strip()
            }
    return titles
