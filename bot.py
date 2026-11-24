import os
import logging
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# --- Educational Command Handlers (Keep these as they are) ---

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    await update.message.reply_html(
        f"👋 Hello {user.mention_html()}!\n\n"
        f"I am 🤖 **IA DEL REY**, your educational assistant for learning about Artificial Intelligence.\n\n"
        f"Use /help to see available commands."
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    help_text = (
        "📚 **Available Commands:**\n"
        "/start - Welcome message\n"
        "/help - Show this help message\n"
        "/learn - Get an AI concept explained\n"
        "/quiz - Test your knowledge with a quick question\n"
    )
    await update.message.reply_text(help_text, parse_mode='Markdown')

async def learn(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    fact = (
        "💡 **AI Concept:** What is Machine Learning?\n\n"
        "Machine Learning is a subset of AI that allows systems to learn and improve from experience without being explicitly programmed."
    )
    await update.message.reply_text(fact, parse_mode='Markdown')

async def quiz(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    question = (
        "🧠 **Quick Quiz:**\n"
        "What does 'AI' stand for?\n\n"
        "A) Automated Intelligence\n"
        "B) Artificial Intelligence\n"
        "C) Advanced Integration\n\n"
        "Reply with the letter of your answer."
    )
    await update.message.reply_text(question, parse_mode='Markdown')

# --- Main Application (POLLING VERSION for Background Worker) ---

def main() -> None:
    """Start the bot in polling mode."""
    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    if not token:
        logger.error("TELEGRAM_BOT_TOKEN environment variable not set!")
        return

    # Build the application normally (polling is the default)
    application = ApplicationBuilder().token(token).build()

    # Register command handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("learn", learn))
    application.add_handler(CommandHandler("quiz", quiz))

    logger.info("Bot is starting in polling mode...")
    # run_polling() starts the bot and keeps it running indefinitely
    application.run_polling()

if __name__ == '__main__':
    main()
