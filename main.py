from databaseManager import FirebaseDB, PRDatabase, SQLiteDB
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

# Context Class to Switch Between Strategies
class PRLoggerContext:
    
    def __init__(self, strategy: PRDatabase):
        self._strategy = strategy
    
    def set_strategy(self, strategy: PRDatabase):
        self._strategy = strategy
    
    def log_pr(self, user_id, exercise, weight):
        return self._strategy.log_pr(user_id, exercise, weight)
    
    def delete_pr(self, user_id, exercise):
        return self._strategy.delete_pr(user_id, exercise)
    
    def fetch_prs(self, user_id):
        return self._strategy.fetch_prs(user_id)

# strategy = FirebaseDB()
strategy = SQLiteDB()

logger = PRLoggerContext(strategy)


# Command to start the bot
async def start(update: Update, context) -> None:
    await update.message.reply_text("Welcome to PRLogger! Use /log to log a PR, or /view to see your PRs.")


# Command to log a new PR
async def log_pr(update: Update, context) -> None:
    user_id = update.message.from_user.id
    try:
        exercise = context.args[0]
        weight = context.args[1]
        message = logger.log_pr(user_id, exercise, weight)
        await update.message.reply_text(message)
    except IndexError:
        await update.message.reply_text("Usage: /log <exercise> <weight>")

# Command to delete a PR
async def delete_pr(update: Update, context) -> None:
    user_id = update.message.from_user.id
    try:
        exercise = context.args[0]
        message = logger.delete_pr(user_id, exercise)
        await update.message.reply_text(message)
    except IndexError:
        await update.message.reply_text("Usage: /delete <exercise>")


# Command to view PRs
async def view_prs(update: Update, context) -> None:
    user_id = update.message.from_user.id
    prs = logger.fetch_prs(user_id)
    await update.message.reply_text(f"Your PRs:\n{prs}")


# Main function to start the bot
def main() -> None:
    TELEGRAM_BOT_TOKEN = '7819922893:AAEIe_nWyseC3ZFOlbwJQEurTbZqKt2S6i0'
    app = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()
    bot = app.bot

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("log", log_pr))
    app.add_handler(CommandHandler("delete", delete_pr))
    app.add_handler(CommandHandler("view", view_prs))

    app.run_polling()

if __name__ == '__main__':
    main()