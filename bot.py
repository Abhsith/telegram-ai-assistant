import os
import sys
import time
import logging
from datetime import datetime
from typing import Optional, Tuple, Dict, Any

import requests
from dotenv import load_dotenv
from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

# =========================
# LOAD ENV
# =========================
load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN", "").strip()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "").strip()
ADMIN_NAME = os.getenv("ADMIN_NAME", "admin_name").strip()
BRAND_NAME = os.getenv("BRAND_NAME", "project_brand").strip()
BOT_NAME = os.getenv("BOT_NAME", "telegram_ai_assistant").strip()

# =========================
# CONFIG
# =========================
REQUEST_TIMEOUT = 20
GEMINI_MODELS = [
    "gemini-1.5-flash-latest",
    "gemini-1.5-flash",
    "gemini-1.5-pro-latest",
    "gemini-pro",
]

SUPPORTED_COINS = {
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

# =========================
# LOGGING
# =========================
logging.basicConfig(
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    level=logging.INFO
)
logger = logging.getLogger("valosint_bot")

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
def clear() -> None:
    os.system("clear")

def slow_print(text: str, delay: float = 0.003) -> None:
    for char in text:
        sys.stdout.write(char)
        sys.stdout.flush()
        time.sleep(delay)
    print()

def box_line() -> None:
    print(f"{BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━{RESET}")

def show_banner() -> None:
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
    print(f"{CYAN}{BOLD}                    ◇ AI ◇ CRYPTO ◇ UTILITY ◇{RESET}\n")

    print(f"{BLUE}                      ╭──────────────╮")
    print(f"                      │   {CYAN}{BOLD}{BRAND_NAME.upper()[:12]:^12}{BLUE} │")
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
    slow_print(f"{YELLOW}[*] Registering Telegram handlers...{RESET}")
    slow_print(f"{GREEN}[✓] Terminal interface ready.{RESET}")
    box_line()

def show_ready() -> None:
    print(f"{GREEN}{BOLD}\n[✓] BOT ONLINE{RESET}")
    print(f"{CYAN}Use these commands in Telegram:{RESET}")
    print(f"{WHITE}/start  /help  /menu  /about  /status  /ai  /crypto  /price{RESET}")
    print(f"{MAGENTA}Press CTRL + C to stop the bot.{RESET}\n")
    box_line()

# =========================
# HELPERS
# =========================
def escape_md(text: str) -> str:
    """
    Escape MarkdownV2 special characters if needed later.
    For now we use HTML/plain text more often, but keeping helper is useful.
    """
    chars = r"_*[]()~`>#+-=|{}.!"
    for char in chars:
        text = text.replace(char, f"\\{char}")
    return text

def format_currency_usd(value: float) -> str:
    return f"${value:,.4f}"

def format_currency_idr(value: float) -> str:
    return f"Rp {value:,.0f}"

def resolve_coin(symbol: str) -> Optional[str]:
    return SUPPORTED_COINS.get(symbol.lower().strip())

def get_crypto_price(symbol: str) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
    coin_id = resolve_coin(symbol)
    if not coin_id:
        supported = ", ".join(sorted(set(k.upper() for k in SUPPORTED_COINS if len(k) <= 4)))
        return None, f"Coin '{symbol}' belum didukung.\n\nCoin tersedia: {supported}"

    try:
        url = "https://api.coingecko.com/api/v3/simple/price"
        params = {
            "ids": coin_id,
            "vs_currencies": "usd,idr",
            "include_24hr_change": "true",
        }
        response = requests.get(url, params=params, timeout=REQUEST_TIMEOUT)
        response.raise_for_status()
        data = response.json()

        if coin_id not in data:
            return None, f"Data untuk {symbol.upper()} tidak ditemukan."

        coin_data = data[coin_id]
        result = {
            "symbol": symbol.upper(),
            "coin_id": coin_id,
            "usd": float(coin_data.get("usd", 0)),
            "idr": float(coin_data.get("idr", 0)),
            "change": float(coin_data.get("usd_24h_change", 0)),
        }
        return result, None

    except requests.RequestException as exc:
        logger.error("Crypto API request failed: %s", exc)
        return None, "Gagal mengambil harga crypto. Coba lagi sebentar."
    except Exception as exc:
        logger.exception("Unexpected crypto error: %s", exc)
        return None, f"Gagal mengambil harga crypto: {exc}"

def ask_gemini(prompt: str) -> Tuple[Optional[str], Optional[str]]:
    if not GEMINI_API_KEY:
        return None, "GEMINI_API_KEY belum diisi di file .env"

    headers = {
        "Content-Type": "application/json"
    }

    payload = {
        "contents": [
            {
                "parts": [
                    {"text": prompt}
                ]
            }
        ]
    }

    last_error = None

    for model in GEMINI_MODELS:
        try:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
            response = requests.post(
                url,
                params={"key": GEMINI_API_KEY},
                headers=headers,
                json=payload,
                timeout=REQUEST_TIMEOUT,
            )

            if response.status_code == 404:
                last_error = f"Model {model} tidak tersedia."
                continue

            response.raise_for_status()
            data = response.json()

            candidates = data.get("candidates", [])
            if not candidates:
                last_error = "AI tidak memberikan jawaban."
                continue

            content = candidates[0].get("content", {})
            parts = content.get("parts", [])
            if not parts:
                last_error = "Jawaban AI kosong."
                continue

            text = "".join(part.get("text", "") for part in parts if "text" in part).strip()
            if not text:
                last_error = "Jawaban AI kosong."
                continue

            return text, None

        except requests.RequestException as exc:
            logger.error("Gemini request failed on model %s: %s", model, exc)
            last_error = f"Gagal menggunakan AI pada model {model}: {exc}"
        except Exception as exc:
            logger.exception("Unexpected Gemini error on model %s: %s", model, exc)
            last_error = f"Terjadi kesalahan AI: {exc}"

    return None, last_error or "Gagal menggunakan AI."

def get_status_text() -> str:
    gemini_status = "Configured" if GEMINI_API_KEY else "Not configured"
    return (
        f"📡 <b>Bot Status</b>\n\n"
        f"• Brand: <b>{BRAND_NAME}</b>\n"
        f"• Bot Name: <b>{BOT_NAME}</b>\n"
        f"• Admin: <b>{ADMIN_NAME}</b>\n"
        f"• Runtime: <b>Python + Termux + Telegram</b>\n"
        f"• Gemini API: <b>{gemini_status}</b>\n"
        f"• Started: <b>{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</b>"
    )

# =========================
# COMMANDS
# =========================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    text = (
        f"🤖 <b>{BOT_NAME} aktif!</b>\n\n"
        f"Selamat datang di bot branded <b>{BRAND_NAME}</b>.\n"
        f"Admin: <b>{ADMIN_NAME}</b>\n\n"
        f"Ketik /help untuk melihat perintah."
    )
    await update.message.reply_text(text, parse_mode=ParseMode.HTML)

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    text = (
        "📌 <b>Daftar Command</b>\n\n"
        "/start - Menyalakan respon bot\n"
        "/help - Bantuan command\n"
        "/menu - Menu utama\n"
        "/about - Info bot\n"
        "/status - Status bot\n"
        "/crypto - Daftar coin yang didukung\n"
        "/price btc - Cek harga coin\n"
        "/ai pertanyaan - Tanya AI\n\n"
        "<b>Contoh:</b>\n"
        "/price btc\n"
        "/ai jelaskan apa itu bitcoin secara singkat"
    )
    await update.message.reply_text(text, parse_mode=ParseMode.HTML)

async def menu_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    text = (
        f"🧩 <b>{BRAND_NAME} Bot Menu</b>\n\n"
        "1. /start\n"
        "2. /help\n"
        "3. /about\n"
        "4. /status\n"
        "5. /crypto\n"
        "6. /price btc\n"
        "7. /ai pertanyaan\n\n"
        "Bot ini sudah siap dipakai untuk command dasar."
    )
    await update.message.reply_text(text, parse_mode=ParseMode.HTML)

async def about_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    text = (
        f"💎 <b>{BOT_NAME}</b>\n\n"
        f"Brand: <b>{BRAND_NAME}</b>\n"
        f"Admin: <b>{ADMIN_NAME}</b>\n"
        "Platform: <b>Telegram + Python + Termux</b>\n"
        "Mode: <b>AI + Crypto Utility</b>\n\n"
        "Bot ini dibuat agar terlihat lebih profesional, branded, dan siap digunakan."
    )
    await update.message.reply_text(text, parse_mode=ParseMode.HTML)

async def status_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(get_status_text(), parse_mode=ParseMode.HTML)

async def crypto_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    text = (
        "💹 <b>Coin yang didukung:</b>\n\n"
        "• BTC\n"
        "• ETH\n"
        "• SOL\n"
        "• XRP\n"
        "• BNB\n"
        "• DOGE\n"
        "• ADA\n"
        "• TON\n"
        "• TRX\n\n"
        "<b>Contoh cek harga:</b>\n"
        "/price btc"
    )
    await update.message.reply_text(text, parse_mode=ParseMode.HTML)

async def price_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not context.args:
        await update.message.reply_text(
            "Gunakan format:\n/price btc"
        )
        return

    symbol = context.args[0].lower().strip()
    data, err = get_crypto_price(symbol)

    if err:
        await update.message.reply_text(f"❌ {err}")
        return

    change_emoji = "📈" if data["change"] >= 0 else "📉"

    text = (
        f"💰 <b>Harga {data['symbol']}</b>\n\n"
        f"USD: <b>{format_currency_usd(data['usd'])}</b>\n"
        f"IDR: <b>{format_currency_idr(data['idr'])}</b>\n"
        f"24H: <b>{data['change']:.2f}%</b> {change_emoji}\n"
        f"Source: <b>CoinGecko</b>"
    )
    await update.message.reply_text(text, parse_mode=ParseMode.HTML)

async def ai_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not context.args:
        await update.message.reply_text(
            "Gunakan format:\n/ai pertanyaan kamu"
        )
        return

    prompt = " ".join(context.args).strip()
    if not prompt:
        await update.message.reply_text("Pertanyaan tidak boleh kosong.")
        return

    await update.message.reply_text("🧠 Sedang memproses pertanyaan AI...")

    answer, err = ask_gemini(prompt)
    if err:
        await update.message.reply_text(f"❌ {err}")
        return

    if len(answer) > 4000:
        answer = answer[:4000] + "\n\n...[dipotong]"

    await update.message.reply_text(answer)

async def unknown_error(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    logger.exception("Unhandled exception: %s", context.error)

# =========================
# MAIN
# =========================
def validate_env() -> bool:
    if not BOT_TOKEN:
        print(f"{RED}[!] BOT_TOKEN tidak ditemukan di file .env{RESET}")
        return False
    return True

def main() -> None:
    show_banner()

    if not validate_env():
        return

    try:
        app = ApplicationBuilder().token(BOT_TOKEN).build()

        app.add_handler(CommandHandler("start", start))
        app.add_handler(CommandHandler("help", help_command))
        app.add_handler(CommandHandler("menu", menu_command))
        app.add_handler(CommandHandler("about", about_command))
        app.add_handler(CommandHandler("status", status_command))
        app.add_handler(CommandHandler("crypto", crypto_command))
        app.add_handler(CommandHandler("price", price_command))
        app.add_handler(CommandHandler("ai", ai_command))

        app.add_error_handler(unknown_error)

        show_ready()
        app.run_polling(drop_pending_updates=True)

    except KeyboardInterrupt:
        print(f"\n{YELLOW}[!] Bot dihentikan oleh user.{RESET}")
    except Exception as exc:
        logger.exception("Fatal error while starting bot: %s", exc)
        print(f"{RED}[!] Gagal menjalankan bot: {exc}{RESET}")

if __name__ == "__main__":
    main()
