import os
import telebot
from google import genai
from google.genai import types

# --- НАСТРОЙКИ ---
TELEGRAM_BOT_TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN')
TELEGRAM_CHAT_ID = os.environ.get('TELEGRAM_CHAT_ID')
GEMINI_API_KEY = os.environ.get('OPENAI_API_KEY')
# Проверка наличия ключей
if not all([TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID, OPENAI_API_KEY]):
    print("Ошибка: Один из токенов (Telegram или OpenAI) не найден в Secrets.")
    exit(1)

# Инициализация
bot = telebot.TeleBot(TELEGRAM_BOT_TOKEN)
client = genai.Client(api_key=GEMINI_API_KEY)

def get_raw_news():
    """Ищет 'сырые' новости в DuckDuckGo."""
    print("🔍 Ищу новости...")
    results = []
    try:
        # Ищем больше (10 штук), чтобы у ИИ был выбор
        ddgs = DDGS()
        results = ddgs.news(keywords="biohacking", region="ru-ru", timelimit="d", max_results=10)
    except Exception as e:
        print(f"Ошибка поиска: {e}")
    return results

def analyze_with_gemini(news_items):
    """Просит Gemini выбрать топ-3 и написать саммари."""
    if not news_items:
        return None

    print("🧠 ИИ анализирует статьи с помощью Gemini...")

    # Подготовка данных для ИИ
    data_text = ""
    for i, item in enumerate(news_items):
        data_text += f"{i+1}. {item.get('title')} - {item.get('body')} (Link: {item.get('url')})\n"

    # Промпт (инструкция) для модели
    prompt = (
        f"Ты — аналитик по биохакингу. Вот список новостей за сегодня:\n{data_text}\n\n"
        "Твоя задача:\n"
        "1. Выбери 3 самые значимые и полезные новости (исключи рекламу и 'воду').\n"
        "2. Для каждой новости напиши краткое резюме на русском языке (1-2 предложения).\n"
        "3. Оформи ответ строго в таком формате:\n\n"
        "🧬 **Заголовок новости**\n"
        "Суть: краткое резюме того, о чем речь.\n"
        "[Читать полностью](ссылка)\n\n"
        "(Повтори для 3 новостей)"
    )

    try:
        response = client.models.generate_content(
            model='gemini-2.5-flash', # Быстрая и мощная модель
            contents=prompt,
            config=types.GenerateContentConfig(
                system_instruction="Ты полезный ассистент-исследователь.",
            ),
        )
        return response.text
    except Exception as e:
        print(f"Ошибка Gemini: {e}")
        return None
def send_telegram(text):
    if not text:
        print("Нет текста для отправки.")
        return
    try:
        # Добавляем заголовок и отправляем
        final_msg = f"🗓 **Дайджест биохакинга за сегодня**\n\n{text}"
        bot.send_message(TELEGRAM_CHAT_ID, final_msg, parse_mode='Markdown', disable_web_page_preview=True)
        print("✅ Сообщение отправлено!")
    except Exception as e:
        print(f"Ошибка Телеграм: {e}")

if __name__ == "__main__":
    news = get_raw_news()
    if news:
        summary = analyze_with_gemini(news)
        send_telegram(summary)
    else:
        print("Новости не найдены.")
