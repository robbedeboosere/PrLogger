import os
from databaseManager import FirebaseDB, PRDatabase, SQLiteDB
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
from dotenv import load_dotenv

# Context Class to Switch Between Strategies
class PRLoggerContext:
    def __init__(self):
        self._strategy = None
    
    def set_strategy(self, strategy: PRDatabase):
        self._strategy = strategy
    
    def log_pr(self, user_id, exercise, weight):
        return self._strategy.log_pr(user_id, exercise, weight)
    
    def delete_pr(self, user_id, exercise):
        return self._strategy.delete_pr(user_id, exercise)
    
    def fetch_prs(self, user_id):
        return self._strategy.fetch_prs(user_id)
    
    def fetch_leaderboard(self, exercise):
        return self._strategy.fetch_leaderboard(exercise)


logger = PRLoggerContext()

# Command to start the bot
async def start(update: Update, context) -> None:
    await update.message.reply_text(
        """Welcome to PRLogger!\n 
Use /log <exercise> <weight> to log a PR \n 
Use /view to see your PRs \n
Use /leaderboard <exercise> to see a leaderboard of the group \n
Use /delete <exercise> to delete the latest log of a given exercise"""
    )


# Command to log a new PR
async def log_pr(update: Update, context) -> None:
    user = update.message.from_user.username
    try:
        exercise = context.args[0]
        weight = context.args[1]
        message = logger.log_pr(user, exercise, weight)
        await update.message.reply_text(message)
    except IndexError:
        await update.message.reply_text("Usage: /log <exercise> <weight>")

# Command to delete a PR
async def delete_pr(update: Update, context) -> None:
    user = update.message.from_user.username
    try:
        exercise = context.args[0]
        message = logger.delete_pr(user, exercise)
        await update.message.reply_text(message)
    except IndexError:
        await update.message.reply_text("Usage: /delete <exercise>")


# Command to view PRs
async def view_prs(update: Update, context) -> None:
    user = update.message.from_user.username
    prs = logger.fetch_prs(user)
    await update.message.reply_text(f"Your PRs:\n{prs}")

async def leaderboard(update: Update, context) -> None:
    try:
        exercise = context.args[0]
        leaderboard = logger.fetch_leaderboard(exercise)
        message = "Leaderboard for {}:\n".format(exercise)
        for index, (user, weight) in enumerate(leaderboard):
            message += f"{index + 1}. User {user}: {weight}kg\n"
        await update.message.reply_text(message)
    except IndexError:
        await update.message.reply_text("Usage: /leaderboard <exercise>")


# Main function to start the bot
def main() -> None:
    load_dotenv()
    TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
    app = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()
    bot = app.bot

    database_type = os.getenv('DATABASE')
    match database_type:
        case "sqlite":
            strategy = SQLiteDB()
        case "firebase":
            strategy = FirebaseDB()
        case _:
            strategy = SQLiteDB()
    

    logger.set_strategy(strategy)

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("log", log_pr))
    app.add_handler(CommandHandler("delete", delete_pr))
    app.add_handler(CommandHandler("view", view_prs))
    app.add_handler(CommandHandler("leaderboard", leaderboard))

    app.run_polling()

if __name__ == '__main__':
    main()