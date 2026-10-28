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

# --- Educational Command Handlers ---

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a welcome message explaining the bot's purpose."""
    user = update.effective_user
    await update.message.reply_html(
        f"👋 Hello {user.mention_html()}!\n\n"
        f"I am 🤖 **IA DEL REY**, your educational assistant for learning about Artificial Intelligence.\n\n"
        f"Use /help to see available commands."
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """List available commands."""
    help_text = (
        "📚 **Available Commands:**\n"
        "/start - Welcome message\n"
        "/help - Show this help message\n"
        "/learn - Get an AI concept explained\n"
        "/quiz - Test your knowledge with a quick question\n"
    )
    await update.message.reply_text(help_text, parse_mode='Markdown')

async def learn(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Provide an educational AI fact or explanation."""
    # In a real bot, you would rotate through a database of concepts.
    fact = (
        "💡 **AI Concept:** What is Machine Learning?\n\n"
        "Machine Learning is a subset of AI that allows systems to learn and improve from experience without being explicitly programmed. It focuses on developing computer programs that can access data and use it to learn for themselves."
    )
    await update.message.reply_text(fact, parse_mode='Markdown')

async def quiz(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a simple educational quiz question."""
    question = (
        "🧠 **Quick Quiz:**\n"
        "What does 'AI' stand for?\n\n"
        "A) Automated Intelligence\n"
        "B) Artificial Intelligence\n"
        "C) Advanced Integration\n\n"
        "Reply with the letter of your answer."
    )
    await update.message.reply_text(question, parse_mode='Markdown')

# --- Main Application ---

def main() -> None:
    """Start the bot in webhook mode for Render."""
    # Get the token from Render's environment variables
    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    if not token:
        logger.error("TELEGRAM_BOT_TOKEN environment variable not set!")
        return

    # Build the application
    application = ApplicationBuilder().token(token).updater(None).build()

    # Register command handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("learn", learn))
    application.add_handler(CommandHandler("quiz", quiz))

    # --- Webhook Configuration for Render ---
    # Render provides the PORT and the public URL (RENDER_EXTERNAL_URL)
    port = int(os.environ.get("PORT", "8080"))
    webhook_url = os.environ.get("RENDER_EXTERNAL_URL")
    
    if not webhook_url:
        logger.error("RENDER_EXTERNAL_URL not set. This is required for webhooks on Render.")
        return

    full_webhook_url = f"{webhook_url}/webhook"
    
    # Start the webhook server
    # Telegram will send updates to https://<your-service>.onrender.com/webhook
    application.run_webhook(
        listen="0.0.0.0",
        port=port,
        url_path="webhook",
        webhook_url=full_webhook_url,
    )

if __name__ == '__main__':
    main()
