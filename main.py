import os
from dotenv import load_dotenv
import telebot

# 03@C7:0 ?5@5<5==KE >:@C65=8O
load_dotenv()
# >;CG5=85 B>:5=0 1>B0
TOKEN = os.getenv("TOKEN")
if not TOKEN:
    raise RuntimeError(" .env D09;5 =5B TOKEN")
# %>740=85 >1J5:B0 1>B0
bot = telebot.TeleBot(TOKEN)


@bot.message_handler(commands=['start'])
def start(message):
    bot.reply_to(message, " @825B! / B2>9 ?5@2K9 1>B! 0?8H8 /help")


@bot.message_handler(commands=['help'])
def help_cmd(message):
    bot.reply_to(message, "/start 4 =0G0BL\n/help 4 ?><>IL")


if __name__ == "__main__":
    print(" >B 70?CA:05BAO...")
bot.infinity_polling(skip_pending=True)