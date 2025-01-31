import telebot 
import requests 
import pandas as pd  
import numpy as np 
import mplfinance as mpf 

TOKEN = "7731125348:AAFz8_4sP2smqhd4t3z26HeMCDZLjsYICQg"
bot = telebot.TeleBot(TOKEN)

def get_crypto_data(symbol="BTCUSDT", interval="1h", limit=100):
    url = f"https://api.binance.com/api/v3/klines?symbol={symbol}&interval={interval}&limit={limit}"
    response = requests.get(url).json()

    df = pd.DataFrame(response, columns=["timestamp", "open", "high", "low", "close", "volume", "_", "_", "_", "_", "_", "_"])
    df["timestamp"] = pd.to_datetime(df["timestamp"], unit="ms")
    df["open"] = df["open"].astype(float)
    df["close"] = df["close"].astype(float)
    df["high"] = df["high"].astype(float)
    df["low"] = df["low"].astype(float)
    df["volume"] = df["volume"].astype(float)
    
    return df

def analyze_market(df):
    df["SMA_20"] = df["close"].rolling(window=20).mean()

    delta = df["close"].diff()
    gain = np.where(delta > 0, delta, 0)
    loss = np.where(delta < 0, -delta, 0)

    avg_gain = pd.Series(gain).rolling(window=14).mean()
    avg_loss = pd.Series(loss).rolling(window=14).mean()
    rs = avg_gain / avg_loss
    df["RSI"] = 100 - (100 / (1 + rs))

    last_sma = df["SMA_20"].iloc[-1]
    last_rsi = df["RSI"].iloc[-1]
    last_price = df["close"].iloc[-1]

    signal = "⚪ Нейтрально"
    if last_price > last_sma and last_rsi > 50:
        signal = "🟢 Лонг (купувати)"
    elif last_price < last_sma and last_rsi < 50:
        signal = "🔴 Шорт (продавати)"
    
    return signal, last_price, last_sma, last_rsi

@bot.message_handler(commands=["start"])
def start_message(message):
    bot.send_message(message.chat.id, "Привіт! Введіть назву криптовалюти (наприклад, BTCUSDT)")

@bot.message_handler(func=lambda message: True)
def crypto_analysis(message):
    symbol = message.text.upper()
    
    try:
        df = get_crypto_data(symbol, "1h", 100)
        trade_signal, last_price, last_sma, last_rsi = analyze_market(df)

        response = f"📊 {symbol} Аналіз:\n"
        response += f"🔹 Поточна ціна: {last_price} USDT\n"
        response += f"🔹 SMA (20): {last_sma:.2f}\n"
        response += f"🔹 RSI (14): {last_rsi:.2f}\n"
        response += f"📢 Сигнал: {trade_signal}"

        bot.send_message(message.chat.id, response)

    except Exception as e:
        bot.send_message(message.chat.id, "Помилка! Можливо, неправильно вказано символ.")

bot.polling(none_stop=True)
