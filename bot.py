import os
import sys
import time
import logging
from datetime import datetime

import requests
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    ContextTypes,
)

# =========================
# LOAD ENV
# =========================
load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
ADMIN_NAME = os.getenv("ADMIN_NAME", "Abdul Bhasit")
BRAND_NAME = os.getenv("BRAND_NAME", "VALOSINT")
BOT_NAME = os.getenv("BOT_NAME", "Telegram AI Assistant")

# =========================
# LOGGING
# =========================
logging.basicConfig(
    format="%(asctime)s | %(levelname)s | %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# =========================
# COLORS FOR TERMUX
# =========================
RESET = "\033[0m"
BOLD = "\033[1m"
CYAN = "\033[96m"
BLUE = "\033[94m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
RED = "\033[91m"
MAGENTA = "\033[95m"
WHITE = "\033[97m"

# =========================
# TERMINAL UI
# =========================
def clear():
    os.system("clear")

def slow_print(text, delay=0.004):
    for char in text:
        sys.stdout.write(char)
        sys.stdout.flush()
        time.sleep(delay)
    print()

def box_line():
    print(f"{BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━{RESET}")

def show_banner():
    clear()
    print(f"""{CYAN}{BOLD}
██╗   ██╗ █████╗ ██╗      ██████╗ ███████╗██╗███╗   ██╗████████╗
██║   ██║██╔══██╗██║     ██╔═══██╗██╔════╝██║████╗  ██║╚══██╔══╝
██║   ██║███████║██║     ██║   ██║███████╗██║██╔██╗ ██║   ██║
╚██╗ ██╔╝██╔══██║██║     ██║   ██║╚════██║██║██║╚██╗██║   ██║
 ╚████╔╝ ██║  ██║███████╗╚██████╔╝███████║██║██║ ╚████║   ██║
  ╚═══╝  ╚═╝  ╚═╝╚══════╝ ╚═════╝ ╚══════╝╚═╝╚═╝  ╚═══╝   ╚═╝
{RESET}""")
    print(f"{WHITE}{BOLD}                 {BOT_NAME} • TELEGRAM BOT{RESET}")
    print(f"{CYAN}{BOLD}                        ◇ AI ◇ CRYPTO ◇{RESET}\n")

    print(f"{BLUE}                      ╭──────────────╮")
    print(f"                      │   {CYAN}{BOLD}VALOSINT{BLUE}   │")
    print(f"                      ╰──────────────╯{RESET}")

    box_line()
    print(f"{GREEN} Brand      : {WHITE}{BRAND_NAME}{RESET}")
    print(f"{GREEN} Admin      : {WHITE}{ADMIN_NAME}{RESET}")
    print(f"{GREEN} Bot Name   : {WHITE}{BOT_NAME}{RESET}")
    print(f"{GREEN} Runtime    : {WHITE}Python + Termux + Telegram{RESET}")
    print(f"{GREEN} Started At : {WHITE}{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}{RESET}")
    box_line()
    slow_print(f"{YELLOW}[*] Initializing bot system...{RESET}")
    slow_print(f"{YELLOW}[*] Loading environment variables...{RESET}")
    slow_print(f"{YELLOW}[*] Preparing Telegram handlers...{RESET}")
    slow_print(f"{GREEN}[✓] Terminal interface ready.{RESET}")
    box_line()

def show_ready():
    print(f"{GREEN}{BOLD}\n[✓] BOT ONLINE{RESET}")
    print(f"{CYAN}Use these commands in Telegram:{RESET}")
    print(f"{WHITE}/start  /help  /menu  /about  /ai  /crypto  /price{RESET}")
    print(f"{MAGENTA}Press CTRL + C to stop the bot.{RESET}\n")
    box_line()

# =========================
# HELPERS
# =========================
CRYPTO_MAP = {
    "btc": "bitcoin",
    "bitcoin": "bitcoin",
    "eth": "ethereum",
    "ethereum": "ethereum",
    "sol": "solana",
    "solana": "solana",
    "xrp": "ripple",
    "ripple": "ripple",
    "bnb": "binancecoin",
    "doge": "dogecoin",
    "dogecoin": "dogecoin",
    "ada": "cardano",
    "cardano": "cardano",
    "ton": "the-open-network",
    "trx": "tron",
}

def get_crypto_price(symbol: str):
    coin_id = CRYPTO_MAP.get(symbol.lower())
    if not coin_id:
        return None, f"Coin '{symbol}' belum didukung."

    try:
        url = "https://api.coingecko.com/api/v3/simple/price"
        params = {
            "ids": coin_id,
            "vs_currencies": "usd,idr",
            "include_24hr_change": "true"
        }
        r = requests.get(url, params=params, timeout=10)
        r.raise_for_status()
        data = r.json()

        if coin_id not in data:
            return None, f"Data untuk {symbol.upper()} tidak ditemukan."

        coin = data[coin_id]
        usd = coin.get("usd", 0)
        idr = coin.get("idr", 0)
        change = coin.get("usd_24h_change", 0)

        result = {
            "symbol": symbol.upper(),
            "usd": usd,
            "idr": idr,
            "change": change
        }
        return result, None

    except Exception as e:
        return None, f"Gagal mengambil harga crypto: {e}"

def ask_gemini(prompt: str):
    if not GEMINI_API_KEY:
        return None, "GEMINI_API_KEY belum diisi di file .env"

    try:
        url = (
            "https://generativelanguage.googleapis.com/v1beta/models/"
            "gemini-1.5-flash:generateContent"
        )
        params = {"key": GEMINI_API_KEY}
        payload = {
            "contents": [
                {
                    "parts": [
                        {"text": prompt}
                    ]
                }
            ]
        }

        r = requests.post(url, params=params, json=payload, timeout=30)
        r.raise_for_status()
        data = r.json()

        text = (
            data["candidates"][0]["content"]["parts"][0]["text"]
            if "candidates" in data and data["candidates"]
            else "AI tidak memberikan jawaban."
        )
        return text, None

    except Exception as e:
        return None, f"Gagal menggunakan AI: {e}"

# =========================
# COMMANDS
# =========================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (
        f"🤖 *{BOT_NAME} aktif!*\n\n"
        f"Selamat datang di bot branded *{BRAND_NAME}*.\n"
        f"Admin: *{ADMIN_NAME}*\n\n"
        f"Ketik /help untuk melihat perintah."
    )
    await update.message.reply_text(text, parse_mode="Markdown")

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (
        "📌 *Daftar Command*\n\n"
        "/start - Menyalakan respon bot\n"
        "/help - Bantuan command\n"
        "/menu - Menu utama\n"
        "/about - Info bot\n"
        "/crypto - Daftar coin yang didukung\n"
        "/price btc - Cek harga coin\n"
        "/ai pertanyaan - Tanya AI\n\n"
        "Contoh:\n"
        "`/price btc`\n"
        "`/ai jelaskan apa itu bitcoin secara singkat`"
    )
    await update.message.reply_text(text, parse_mode="Markdown")

async def menu_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (
        f"🧩 *{BRAND_NAME} Bot Menu*\n\n"
        "1. /start\n"
        "2. /help\n"
        "3. /about\n"
        "4. /crypto\n"
        "5. /price btc\n"
        "6. /ai pertanyaan\n\n"
        "Bot ini sudah siap dipakai untuk command dasar."
    )
    await update.message.reply_text(text, parse_mode="Markdown")

async def about_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (
        f"💎 *{BOT_NAME}*\n\n"
        f"Brand: *{BRAND_NAME}*\n"
        f"Admin: *{ADMIN_NAME}*\n"
        "Platform: *Telegram + Python + Termux*\n"
        "Mode: *AI + Crypto Utility*\n\n"
        "Bot ini dibuat agar terlihat lebih profesional, branded, dan siap digunakan."
    )
    await update.message.reply_text(text, parse_mode="Markdown")

async def crypto_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (
        "💹 *Coin yang didukung:*\n\n"
        "- BTC\n"
        "- ETH\n"
        "- SOL\n"
        "- XRP\n"
        "- BNB\n"
        "- DOGE\n"
        "- ADA\n"
        "- TON\n"
        "- TRX\n\n"
        "Contoh cek harga:\n"
        "`/price btc`"
    )
    await update.message.reply_text(text, parse_mode="Markdown")

async def price_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text(
            "Gunakan format:\n`/price btc`",
            parse_mode="Markdown"
        )
        return

    symbol = context.args[0].lower()
    data, err = get_crypto_price(symbol)

    if err:
        await update.message.reply_text(f"❌ {err}")
        return

    change_emoji = "📈" if data["change"] >= 0 else "📉"
    text = (
        f"💰 *Harga {data['symbol']}*\n\n"
        f"USD: `${data['usd']:,.4f}`\n"
        f"IDR: `Rp {data['idr']:,.0f}`\n"
        f"24H: `{data['change']:.2f}%` {change_emoji}"
    )
    await update.message.reply_text(text, parse_mode="Markdown")

async def ai_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text(
            "Gunakan format:\n`/ai pertanyaan kamu`",
            parse_mode="Markdown"
        )
        return

    prompt = " ".join(context.args)
    await update.message.reply_text("🧠 Sedang memproses pertanyaan AI...")

    answer, err = ask_gemini(prompt)
    if err:
        await update.message.reply_text(f"❌ {err}")
        return

    if len(answer) > 4000:
        answer = answer[:4000] + "\n\n...[dipotong]"
    await update.message.reply_text(answer)

async def unknown_error(update: object, context: ContextTypes.DEFAULT_TYPE):
    logger.error("Unhandled exception:", exc_info=context.error)

# =========================
# MAIN
# =========================
def main():
    show_banner()

    if not BOT_TOKEN:
        print(f"{RED}[!] BOT_TOKEN tidak ditemukan di file .env{RESET}")
        return

    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("menu", menu_command))
    app.add_handler(CommandHandler("about", about_command))
    app.add_handler(CommandHandler("crypto", crypto_command))
    app.add_handler(CommandHandler("price", price_command))
    app.add_handler(CommandHandler("ai", ai_command))

    app.add_error_handler(unknown_error)

    show_ready()
    app.run_polling()

if __name__ == "__main__":
    main()
