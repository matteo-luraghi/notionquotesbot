# 📚 Quotes Bot - Your Daily Dose of Wisdom 📖

Welcome to **Quotes Bot**! This Telegram bot connects to your Notion database filled with book quotes, delivering a touch of inspiration straight to your chat. Whether you're looking for a random quote to brighten your day or searching for something specific from your favorite author or book, Quotes Bot has got you covered!

## 🚀 Features

- 🎲 **/quote** - Sends a random quote from the database.
- 🖋️ **/author {name}** - Sends all quotes from the specified author.
- 📝 **/authors** - Lists all authors and sends all quotes from them.
- 📖 **/title {book}** - Sends all quotes from the specified book.
- 📚 **/titles** - Lists all books and sends all quotes from the selected one.
- ✍️  **/titleauthor {name}** - Lists all books by the specified author and sends all quotes from them.
- 📅 **Daily Quote** - Automatically sends a random quote from a random book every morning.

## 🛠️ Setup Instructions

1. **Clone the repository**
   ```bash
   git clone https://github.com/matteo-luraghi/notionquotesbot.git
   cd quotebot
   ```
2. **Create a Telegram Bot**
   - Talk to [BotFather](https://telegram.me/BotFather) on Telegram.
   - Use the **/newbot** command to create your bot and get the API token.
3. **Set up Notion Integration**
   - Go to [Notion Developers](https://developers.notion.com/) and create a new [integration](https://www.notion.so/profile/integrations).
   - Duplicate the [template](https://cold-market-982.notion.site/795b385cfa41464fac7c1106d436b1a7?v=818bdc289cda47458f4e0fd676738134&pvs=4) to create your own database
   - Share your Notion database with the integration by going to your database, clicking "Share," and adding your integration.
4. **Configure Environment Variables**
   - Create a `config.py` file in the project `/app` directory with the following content: `API_KEY="your-telegram-api-key"`
5. **Run the bot**
   - Run the bot using docker:
     ```bash
     docker compose up --build
     ```
   - Use the **/start** command to setup the connection with your Notion database

## 🌟 Usage

Once the bot is running, invite it to your Telegram group or chat with it directly. Use the commands listed above to interact with your quote database.

## 📝 License

This project is licensed under the [MIT LICENSE](LICENSE).
