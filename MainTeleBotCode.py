import telebot
import time
import threading
from tradingview_ta import TA_Handler, Interval

# توكن البوت من BotFather
TOKEN = "7857687043:AAEZmasAeHC1Egjx7iVPQFs-KJBi9cscjJE"
bot = telebot.TeleBot(TOKEN)

# معرف القنوات
SOURCE_USERNAME = "TQks89"  # استبدل هذا بمعرف القناة المصدر بدون @
TARGET_USERNAME = "tkZoro"  # استبدل هذا بمعرف القناة الهدف بدون @
GROUP_CHAT_USERNAME = "twrsichannel"  # استبدل هذا بمعرف القروب بدون @

# إعدادات RSI
OVERBOUGHT = 70
OVERSOLD = 30
CHECK_INTERVAL = 900  # التحقق كل 15 دقيقة

# تحميل الرموز من ملف
def load_symbols(file_path):
    symbols = []
    try:
        with open(file_path, 'r') as file:
            for line in file:
                symbol = line.strip()
                if symbol:  # تأكد أن السطر ليس فارغاً
                    symbols.append({"symbol": symbol, "exchange": "BINANCE"})
    except FileNotFoundError:
        print("الملف symbols.txt غير موجود، يرجى التأكد من مساره.")
    return symbols

# تحميل أفضل 1000 عملة
SYMBOLS = load_symbols('symbols.txt')

# تابع لتحويل الصور من القناة المصدر إلى القناة الهدف
@bot.channel_post_handler(content_types=['photo'], func=lambda message: message.chat.username == SOURCE_USERNAME)
def forward_photos(message):
    try:
        bot.forward_message(f"@{TARGET_USERNAME}", message.chat.id, message.message_id)
        print(f"تم تحويل الصورة من @{SOURCE_USERNAME} إلى @{TARGET_USERNAME}")
    except Exception as e:
        print(f"خطأ في تحويل الصورة: {e}")

# دالة لجلب RSI من TradingView باستخدام python-tradingview-ta
def get_rsi_from_tradingview(symbol, exchange):
    try:
        handler = TA_Handler(
            symbol=symbol,
            exchange=exchange,
            screener="crypto",
            interval=Interval.INTERVAL_1_DAY
        )
        analysis = handler.get_analysis()
        rsi = analysis.indicators['RSI']
        return rsi
    except Exception as e:
        print(f"خطأ في جلب RSI من TradingView للرمز {symbol}: {e}")
        return None

# دالة للتحقق من RSI للعملات المتعددة
def check_rsi():
    while True:
        for asset in SYMBOLS:
            symbol = asset["symbol"]
            exchange = asset["exchange"]
            try:
                latest_rsi = get_rsi_from_tradingview(symbol, exchange)

                if latest_rsi is not None:
                    if latest_rsi >= OVERBOUGHT:
                        bot.send_message(f"@{GROUP_CHAT_USERNAME}", f"🔴 تنبيه: {symbol} وصل إلى ذروة الشراء - RSI = {latest_rsi:.2f}")
                    elif latest_rsi <= OVERSOLD:
                        bot.send_message(f"@{GROUP_CHAT_USERNAME}", f"🟢 تنبيه: {symbol} وصل إلى ذروة البيع - RSI = {latest_rsi:.2f}")
                    
                    print(f"RSI للرمز {symbol}: {latest_rsi:.2f}")
                else:
                    print(f"لم يتم الحصول على RSI صالح للرمز {symbol}")
            except Exception as e:
                print(f"خطأ في التحقق من RSI للرمز {symbol}: {e}")
        time.sleep(CHECK_INTERVAL)

# تشغيل البوت والتحقق من RSI في خيطين منفصلين
def start_bot():
    print("تشغيل البوت للتحويل وتنبيهات RSI...")
    bot.polling(none_stop=True)

bot_thread = threading.Thread(target=start_bot)
rsi_thread = threading.Thread(target=check_rsi)

bot_thread.start()
rsi_thread.start()
